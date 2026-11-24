"""Dienstbetrieb: start, status, stop, Sperre, Scheduler und systemd-Unit (T182)."""
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from scripts import service

REPO = Path(__file__).resolve().parents[1]


def make_root(tmp):
    root = Path(tmp)
    shutil.copytree(REPO / 'scripts', root / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(REPO / 'deploy', root / 'deploy')
    for name in ('config.example.json', 'config.schema.json', 'start.sh', 'stop.sh', 'status.sh'):
        shutil.copy2(REPO / name, root / name)
    shutil.copy2(REPO / 'config.example.json', root / 'config.json')
    (root / 'out' / 'public').mkdir(parents=True)
    (root / 'out' / 'public' / 'index.html').write_text('hallo', encoding='utf-8')
    return root


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class FakeHandle:
    def __init__(self, pid=999_999, code=None):
        self.pid, self.returncode, self._code = pid, code, code

    def poll(self):
        return self._code


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = make_root(tmp.name)
        self.launched = []
        self.due = {'due': True, 'slot_utc': '2027-01-01T06:05:00+00:00'}

    def svc(self):
        def launch(show):
            self.launched.append(show)
            self.handle = FakeHandle()
            return self.handle
        instance = service.Service(self.root, port=free_port(), tick=5, due_fn=lambda show: self.due, launch_fn=launch)
        self.addCleanup(lambda: instance.server and (instance.server.shutdown(), instance.server.server_close()))
        return instance

    def test_due_show_starts_one_job_and_not_twice(self):
        instance = self.svc()
        instance.tick()
        instance.tick()
        self.assertEqual(self.launched, ['main'])
        self.assertEqual(json.loads(service.service_paths(self.root)['state'].read_text())['jobs']['main']['slot'], self.due['slot_utc'])

    def test_finished_slot_is_not_produced_again_after_restart(self):
        first = self.svc()
        first.tick()
        self.handle._code, self.handle.returncode = 0, 0
        first.tick()
        self.assertEqual(self.launched, ['main'])
        second = self.svc()  # new process, state read from disk
        second.tick()
        self.assertEqual(self.launched, ['main'])
        self.due = {'due': True, 'slot_utc': '2027-01-01T12:05:00+00:00'}
        second.tick()
        self.assertEqual(self.launched, ['main', 'main'])

    def test_failed_job_is_retried_on_next_tick(self):
        instance = self.svc()
        instance.tick()
        self.handle._code, self.handle.returncode = 1, 1
        instance.tick()
        self.assertEqual(self.launched, ['main', 'main'])
        self.assertIn('Code 1', instance.state['last_error'])

    def test_not_due_and_config_errors_are_reported(self):
        self.due = {'due': False, 'slot_utc': None}
        instance = self.svc()
        instance.tick()
        self.assertEqual(self.launched, [])
        self.assertEqual(instance.state['scheduler'], 'ok')
        (self.root / 'config.json').write_text('{kaputt', encoding='utf-8')
        instance.tick()
        self.assertEqual(instance.state['scheduler'], 'error')

    def test_http_serves_public_directory_on_loopback_and_recovers(self):
        shutil.rmtree(self.root / 'out' / 'public')
        instance = self.svc()
        instance.tick()
        self.assertTrue(instance.state['http']['status'].startswith('unavailable'))
        (self.root / 'out' / 'public').mkdir()
        (self.root / 'out' / 'public' / 'index.html').write_text('da', encoding='utf-8')
        instance.tick()
        self.assertEqual(instance.state['http']['status'], 'ok')
        with socket.create_connection(('127.0.0.1', instance.port), timeout=3) as conn:
            conn.sendall(b'GET / HTTP/1.0\r\n\r\n')
            received = b''
            while chunk := conn.recv(4096):
                received += chunk
            self.assertTrue(received.endswith(b'da'))
        self.assertEqual(instance.state['http']['bind'], '127.0.0.1')

    def test_shutdown_marks_running_jobs_interrupted(self):
        instance = self.svc()
        instance.tick()
        instance.jobs['main']['handle'] = FakeHandle()
        instance.terminate_job = lambda job: None
        instance.shutdown(grace=0)
        state = json.loads(service.service_paths(self.root)['state'].read_text())
        self.assertEqual(state['status'], 'stopped')
        self.assertEqual(state['interrupted'][0]['show'], 'main')
        self.assertEqual(state['jobs'], {})

    def test_dead_job_from_previous_run_is_detected_on_adoption(self):
        paths = service.service_paths(self.root)
        service.write_state(paths, {'jobs': {'main': {'pid': 999_998, 'slot': 'x'}}})
        instance = self.svc()
        instance.adopt_previous_jobs()
        self.assertEqual(instance.jobs, {})
        self.assertEqual(instance.state['interrupted'][0]['slot'], 'x')


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = make_root(tmp.name)
        self.env = {**os.environ, 'PNH_PORT': str(free_port()), 'PNH_TICK_SECONDS': '5'}
        self.addCleanup(lambda: self.sh('stop.sh'))

    def sh(self, script, *args):
        return subprocess.run(['bash', str(self.root / script), *args], cwd=self.root, env=self.env,
                              capture_output=True, text=True, timeout=120)

    def test_start_status_stop_restart_are_idempotent(self):
        self.assertEqual(self.sh('status.sh').returncode, service.EXIT_STOPPED)
        self.assertEqual(self.sh('stop.sh').returncode, 0)  # stopping a stopped service is safe
        first = self.sh('start.sh')
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.sh('start.sh')
        self.assertIn('läuft bereits', second.stdout)
        status = self.sh('status.sh')
        report = json.loads(status.stdout)
        self.assertEqual((status.returncode, report['running'], report['mode']), (0, True, 'manual'))
        pid = report['pid']
        self.assertTrue(service.process_is_ours(pid, self.root))
        with socket.create_connection(('127.0.0.1', int(self.env['PNH_PORT'])), timeout=3):
            pass
        self.assertEqual(self.sh('stop.sh').returncode, 0)
        self.assertFalse(service.pid_alive(pid) and service.process_is_ours(pid, self.root))
        self.assertEqual(self.sh('status.sh').returncode, service.EXIT_STOPPED)
        self.assertEqual(self.sh('start.sh').returncode, 0)  # restart works
        self.assertTrue(json.loads(self.sh('status.sh').stdout)['running'])

    def test_second_run_in_foreground_is_refused_by_the_lock(self):
        self.assertEqual(self.sh('start.sh').returncode, 0)
        other = subprocess.run([sys.executable, str(self.root / 'scripts' / 'service.py'), 'run'], cwd=self.root,
                               env=self.env, capture_output=True, text=True, timeout=30)
        self.assertEqual(other.returncode, service.EXIT_RUNNING)
        self.assertIn('läuft bereits', other.stderr)

    def test_stop_ignores_foreign_lock_holder(self):
        paths = service.service_paths(self.root)
        paths['dir'].mkdir(parents=True)
        holder = subprocess.Popen([sys.executable, '-c', 'import fcntl,os,sys,time;f=os.open(sys.argv[1],os.O_RDWR|os.O_CREAT);'
                                   'fcntl.flock(f,fcntl.LOCK_EX);print("ok",flush=True);time.sleep(30)', str(paths['lock'])],
                                  stdout=subprocess.PIPE, text=True)
        self.addCleanup(holder.kill)
        holder.stdout.readline()
        self.addCleanup(holder.stdout.close)
        service.write_state(paths, {'pid': holder.pid, 'mode': 'manual'})
        result = self.sh('stop.sh')
        self.assertEqual(result.returncode, service.EXIT_FAILED)
        self.assertIsNone(holder.poll())  # foreign process untouched

    def test_systemd_mode_is_not_controlled_by_scripts(self):
        proc = subprocess.Popen([sys.executable, str(self.root / 'scripts' / 'service.py'), 'run', '--managed', 'systemd'],
                                cwd=self.root, env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: (proc.send_signal(signal.SIGTERM), proc.wait(timeout=30)))
        paths = service.service_paths(self.root)
        for _ in range(50):
            if service.read_state(paths).get('mode') == 'systemd':
                break
            time.sleep(0.1)
        stop = self.sh('stop.sh')
        self.assertEqual(stop.returncode, service.EXIT_FAILED)
        self.assertIn('systemctl --user stop', stop.stdout)
        self.assertIn('systemctl --user start', self.sh('start.sh').stdout)
        self.assertIsNone(proc.poll())

    def test_job_children_are_stopped_with_the_service(self):
        instance = service.Service(self.root, port=free_port(), tick=5, due_fn=lambda s: {'due': False})
        child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)  # local_runtime.py ' + str(self.root)],
                                 start_new_session=True)
        self.addCleanup(child.kill)
        instance.jobs['main'] = {'pid': child.pid, 'slot': 's', 'handle': child}
        instance.terminate_job(instance.jobs['main'])
        self.assertIsNotNone(child.poll())


class SystemdUnitTests(unittest.TestCase):
    def test_unit_is_rendered_installed_and_not_overwritten_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tempfile.mkdtemp(dir=tmp))
            home = Path(tmp) / 'home'
            self.assertEqual(service.main(['install-systemd', '--home', str(home), '--python', '/opt/py/bin/python'], root=root), 0)
            unit = service.unit_target(home).read_text(encoding='utf-8')
            self.assertIn(f'ExecStart=/opt/py/bin/python {root}/scripts/service.py run --managed systemd', unit)
            self.assertIn(f'WorkingDirectory={root}', unit)
            self.assertNotIn('@ROOT@', unit)
            self.assertNotIn('@PYTHON@', unit)
            self.assertEqual(service.main(['install-systemd', '--home', str(home), '--python', '/opt/py/bin/python'], root=root), 0)
            self.assertEqual(service.main(['install-systemd', '--home', str(home), '--python', '/other/python'], root=root), service.EXIT_FAILED)
            self.assertEqual(service.main(['install-systemd', '--home', str(home), '--python', '/other/python', '--force'], root=root), 0)
            self.assertEqual(service.main(['uninstall-systemd', '--home', str(home)], root=root), 0)
            self.assertFalse(service.unit_target(home).exists())

    @unittest.skipUnless(shutil.which('systemd-analyze'), 'systemd-analyze fehlt')
    def test_unit_passes_systemd_analyze_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp)
            unit = Path(tmp) / 'personalnewshost.service'
            unit.write_text(service.unit_text(root, sys.executable), encoding='utf-8')
            result = subprocess.run(['systemd-analyze', '--user', 'verify', str(unit)], capture_output=True, text=True, timeout=60)
            self.assertNotIn('Unknown key', result.stderr + result.stdout)
            self.assertNotIn('Failed to parse', result.stderr + result.stdout)


if __name__ == '__main__':
    unittest.main()
