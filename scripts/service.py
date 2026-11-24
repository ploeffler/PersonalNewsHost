#!/usr/bin/env python3
"""Dauerbetrieb unter Linux: Scheduler und lokale HTTP-Auslieferung als ein Dienst (T182).

Befehle: ``run`` (Vordergrund, auch für systemd), ``start`` (im Hintergrund),
``stop``, ``status``, ``install-systemd``/``uninstall-systemd``.

* Genau eine Instanz je Projektordner: exklusive Sperre ``state/service/service.lock``
  (der Kernel gibt sie beim Prozessende frei; es gibt keine veralteten Sperren).
* ``stop`` signalisiert nur den eigenen, geprüften Dienstprozess. Der Dienst beendet
  den Scheduler, wartet auf laufende Produktionsläufe und beendet sie erst nach
  Ablauf der Frist geordnet (SIGTERM an die eigene Prozessgruppe).
* Zustand für die Wiederaufnahme: ``state/service/state.json`` (Zeitpunkte, laufende
  und unterbrochene Aufträge, zuletzt produzierte Slots). Ein Neustart startet eine
  Sendung nur, wenn der Slot fällig ist und noch nicht produziert wurde.
* Betriebsart ``systemd`` (``run --managed systemd``) und manuelle Skripte werden
  getrennt: Läuft der Dienst unter systemd, verweisen start/stop darauf.
"""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

try:
    from . import local_runtime
except ImportError:
    import local_runtime

ROOT = Path(__file__).resolve().parents[1]
UNIT_NAME = 'personalnewshost.service'
EXIT_RUNNING, EXIT_STOPPED, EXIT_FAILED = 0, 3, 1
DEFAULT_TICK, DEFAULT_PORT, STOP_GRACE = 60, 8080, 90


def service_paths(root=ROOT):
    folder = Path(root).resolve() / 'state' / 'service'
    return {'dir': folder, 'lock': folder / 'service.lock', 'pid': folder / 'service.pid',
            'state': folder / 'state.json', 'log': folder / 'service.log'}


def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def read_state(paths):
    try:
        value = json.loads(paths['state'].read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write_state(paths, state):
    paths['dir'].mkdir(parents=True, exist_ok=True)
    temporary = paths['state'].with_name('.state.json.tmp')
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, paths['state'])


def lock_held(paths):
    """True if another process holds the instance lock."""
    try:
        descriptor = os.open(paths['lock'], os.O_RDWR)
    except OSError:
        return False
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        return False
    except OSError:
        return True
    finally:
        os.close(descriptor)


def acquire_lock(paths):
    paths['dir'].mkdir(parents=True, exist_ok=True)
    descriptor = os.open(paths['lock'], os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(descriptor)
        return None
    return descriptor


def process_is_ours(pid, root=ROOT, markers=('service.py', 'local_runtime.py')):
    """The process exists, belongs to this user and was started from this project."""
    try:
        command = Path(f'/proc/{int(pid)}/cmdline').read_bytes().split(b'\0')
        if Path(f'/proc/{int(pid)}').stat().st_uid != os.getuid():
            return False
    except (OSError, ValueError):
        return False
    text = ' '.join(part.decode('utf-8', 'replace') for part in command)
    return str(Path(root).resolve()) in text and any(marker in text for marker in markers)


def pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


class Service:
    """Scheduler loop; clock, due-check and job launch are injectable for tests."""

    def __init__(self, root=ROOT, config=None, port=DEFAULT_PORT, tick=DEFAULT_TICK, managed='manual',
                 due_fn=None, launch_fn=None, clock=None):
        self.root, self.paths = Path(root).resolve(), service_paths(root)
        self.layout = local_runtime.layout(self.root)
        self.config = Path(config) if config else self.layout['config']
        self.port, self.tick_seconds, self.managed = port, tick, managed
        self.due_fn = due_fn or (lambda show: local_runtime.due(self.config, show, self.layout, self.clock()))
        self.launch_fn = launch_fn or self._launch
        self.clock = clock or (lambda: dt.datetime.now(dt.timezone.utc))
        self.stop_event = threading.Event()
        self.jobs, self.server, self.http_thread = {}, None, None
        self.state = read_state(self.paths)
        self.state.setdefault('produced', {})

    # --- jobs -------------------------------------------------------------
    def _launch(self, show):
        command = [sys.executable, str(Path(__file__).with_name('local_runtime.py')), 'produce',
                   '--config', str(self.config), '--show', show]
        log = open(self.paths['log'], 'ab')
        return subprocess.Popen(command, cwd=self.root, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                start_new_session=True)

    def _job_running(self, job):
        handle = job.get('handle')
        if handle is not None:
            return handle.poll() is None
        return pid_alive(job['pid']) and process_is_ours(job['pid'], self.root)

    def reap(self):
        for show, job in list(self.jobs.items()):
            if self._job_running(job):
                continue
            handle = job.get('handle')
            code = handle.returncode if handle is not None else None
            self.state['produced'][show] = job['slot']
            if code not in (0, None):
                self.state['produced'].pop(show, None)
                self.state['last_error'] = f'Produktionslauf {show} endete mit Code {code}'
            self.state['last_production'] = {'show': show, 'slot': job['slot'], 'finished_at': now_iso(), 'exit_code': code}
            del self.jobs[show]

    def adopt_previous_jobs(self):
        """Resume bookkeeping after a restart: live own jobs are kept, dead ones are marked interrupted."""
        for show, job in (self.state.get('jobs') or {}).items():
            if pid_alive(job.get('pid')) and process_is_ours(job['pid'], self.root):
                self.jobs[show] = {'pid': job['pid'], 'slot': job.get('slot'), 'handle': None}
            else:
                self.state.setdefault('interrupted', []).append({'show': show, 'slot': job.get('slot'), 'detected_at': now_iso()})
        self.state['jobs'] = {}

    # --- scheduler ----------------------------------------------------------
    def shows(self):
        try:
            from .shows import resolve_shows
        except ImportError:
            from shows import resolve_shows
        return [item['id'] for item in resolve_shows(json.loads(self.config.read_text(encoding='utf-8')))]

    def tick(self):
        self.reap()
        errors = []
        try:
            ids = self.shows()
        except (OSError, ValueError) as exc:
            ids, errors = [], [f'Konfiguration: {type(exc).__name__}']
        for show in ids:
            if show in self.jobs or self.stop_event.is_set():
                continue
            try:
                result = self.due_fn(show)
            except (OSError, ValueError) as exc:
                errors.append(f'{show}: {type(exc).__name__}')
                continue
            slot = result.get('slot_utc')
            if not result.get('due') or self.state['produced'].get(show) == slot:
                continue
            handle = self.launch_fn(show)
            self.jobs[show] = {'pid': handle.pid, 'slot': slot, 'handle': handle}
            self.state['produced'].pop(show, None)
        self.ensure_http()
        self.save(errors)

    # --- http -------------------------------------------------------------
    def ensure_http(self):
        if self.server is not None:
            return
        try:
            self.server = local_runtime.preview_server(self.layout, self.port)
        except (OSError, ValueError) as exc:
            self.http_error = f'{type(exc).__name__}'
            return
        self.http_error = ''
        self.http_thread = threading.Thread(target=self.server.serve_forever, name='pnh-http', daemon=True)
        self.http_thread.start()

    http_error = ''

    # --- state ------------------------------------------------------------
    def save(self, errors=(), status='running'):
        self.state.update({
            'status': status, 'pid': os.getpid(), 'mode': self.managed, 'updated_at': now_iso(),
            'started_at': self.state.get('started_at') or now_iso(), 'tick_seconds': self.tick_seconds,
            'scheduler': 'ok' if not errors else 'error', 'errors': list(errors)[:5],
            'http': {'port': self.port, 'bind': '127.0.0.1',
                     'status': 'ok' if self.server is not None and self.http_thread and self.http_thread.is_alive()
                     else ('unavailable: ' + self.http_error if self.http_error else 'stopped')},
            'jobs': {show: {'pid': job['pid'], 'slot': job['slot']} for show, job in self.jobs.items()}})
        write_state(self.paths, self.state)

    # --- lifecycle ----------------------------------------------------------
    def run(self):
        self.state['started_at'] = now_iso()
        self.adopt_previous_jobs()
        for name in (signal.SIGTERM, signal.SIGINT):
            signal.signal(name, lambda *_: self.stop_event.set())
        self.save()
        while not self.stop_event.is_set():
            try:
                self.tick()
            except Exception as exc:  # the loop must survive a bad tick
                self.state['last_error'] = f'tick: {type(exc).__name__}'
            self.stop_event.wait(self.tick_seconds)
        self.shutdown()

    def shutdown(self, grace=STOP_GRACE):
        self.stop_event.set()
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        deadline = time.monotonic() + grace
        while self.jobs and time.monotonic() < deadline:
            self.reap()
            time.sleep(0.5)
        for show, job in list(self.jobs.items()):
            self.terminate_job(job)
            self.state.setdefault('interrupted', []).append({'show': show, 'slot': job['slot'], 'detected_at': now_iso()})
        self.jobs.clear()
        self.save(status='stopped')

    def terminate_job(self, job):
        """Stop an own job: whole process group, SIGTERM first, SIGKILL after 10 s."""
        pid = job['pid']
        if not process_is_ours(pid, self.root) and job.get('handle') is None:
            return
        for sig, wait in ((signal.SIGTERM, 10), (signal.SIGKILL, 2)):
            try:
                os.killpg(pid, sig)
            except OSError:
                return
            end = time.monotonic() + wait
            while time.monotonic() < end:
                handle = job.get('handle')
                if (handle.poll() is not None) if handle is not None else not pid_alive(pid):
                    return
                time.sleep(0.2)


# --- commands --------------------------------------------------------------
def current(paths, root=ROOT):
    """(running, pid, state) of the service; running means the instance lock is held."""
    state = read_state(paths)
    running = lock_held(paths)
    pid = state.get('pid') if running else None
    if running and not (pid and process_is_ours(pid, root)):
        pid = None
    return running, pid, state


def cmd_run(root, args):
    paths = service_paths(root)
    descriptor = acquire_lock(paths)
    if descriptor is None:
        print('Der Dienst läuft bereits (Sperre belegt); kein zweiter Start.', file=sys.stderr)
        return EXIT_RUNNING
    paths['pid'].write_text(f'{os.getpid()}\n', encoding='utf-8')
    try:
        Service(root, args.config, args.port, args.tick, args.managed).run()
    finally:
        paths['pid'].unlink(missing_ok=True)
        os.close(descriptor)
    return 0


def cmd_start(root, args):
    paths = service_paths(root)
    running, pid, state = current(paths, root)
    if running:
        if state.get('mode') == 'systemd':
            print(f'Der Dienst läuft unter systemd (PID {pid}); bitte `systemctl --user start {UNIT_NAME}` verwenden.')
        else:
            print(f'Der Dienst läuft bereits (PID {pid}).')
        return EXIT_RUNNING
    paths['dir'].mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(Path(__file__).resolve()), 'run', '--port', str(args.port), '--tick', str(args.tick)]
    if args.config:
        command += ['--config', str(args.config)]
    with open(paths['log'], 'ab') as log:
        subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    for _ in range(100):
        time.sleep(0.1)
        running, pid, _ = current(paths, root)
        if running and pid:
            print(f'Dienst gestartet (PID {pid}).')
            return 0
    print(f'Dienst konnte nicht gestartet werden; siehe {paths["log"]}', file=sys.stderr)
    return EXIT_FAILED


def cmd_stop(root, args):
    paths = service_paths(root)
    running, pid, state = current(paths, root)
    if not running:
        print('Der Dienst läuft nicht.')
        return 0
    if state.get('mode') == 'systemd':
        print(f'Der Dienst läuft unter systemd; bitte `systemctl --user stop {UNIT_NAME}` verwenden.')
        return EXIT_FAILED
    if not pid:
        print('Die Sperre wird von einem fremden Prozess gehalten; nichts wird beendet.', file=sys.stderr)
        return EXIT_FAILED
    os.kill(pid, signal.SIGTERM)
    end = time.monotonic() + args.timeout
    while time.monotonic() < end:
        if not lock_held(paths):
            print('Dienst beendet.')
            return 0
        time.sleep(0.2)
    print(f'Der Dienst (PID {pid}) beendet laufende Aufträge noch; später erneut `status` prüfen.', file=sys.stderr)
    return EXIT_FAILED


def cmd_status(root, args):
    paths = service_paths(root)
    running, pid, state = current(paths, root)
    report = {'running': running, 'pid': pid, 'mode': state.get('mode') if running else None,
              'status': state.get('status') if running else state.get('status', 'never started'),
              'started_at': state.get('started_at'), 'updated_at': state.get('updated_at'),
              'scheduler': state.get('scheduler'), 'http': state.get('http'), 'jobs': state.get('jobs', {}),
              'last_production': state.get('last_production'), 'interrupted': state.get('interrupted', []),
              'errors': state.get('errors', []), 'log': str(paths['log'])}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return EXIT_RUNNING if running else EXIT_STOPPED


def unit_text(root=ROOT, python=None):
    template = (Path(root) / 'deploy' / UNIT_NAME).read_text(encoding='utf-8')
    return template.replace('@ROOT@', str(Path(root).resolve())).replace('@PYTHON@', python or sys.executable)


def unit_target(home=None):
    return Path(home or Path.home()) / '.config' / 'systemd' / 'user' / UNIT_NAME


def cmd_install_systemd(root, args):
    text, target = unit_text(root, args.python), unit_target(args.home)
    if target.exists() and target.read_text(encoding='utf-8') != text and not args.force:
        print(f'{target} existiert mit anderem Inhalt; mit --force überschreiben.', file=sys.stderr)
        return EXIT_FAILED
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
    print(f'Unit geschrieben: {target}')
    print(f'Aktivieren: systemctl --user daemon-reload && systemctl --user enable --now {UNIT_NAME}')
    print('Start auch ohne Anmeldung nach einem Neustart: loginctl enable-linger "$USER" (einmalig, braucht Rechte)')
    return 0


def cmd_uninstall_systemd(root, args):
    target = unit_target(args.home)
    if target.exists():
        target.unlink()
        print(f'Unit entfernt: {target}. Danach: systemctl --user disable --now {UNIT_NAME}; systemctl --user daemon-reload')
    else:
        print('Keine Unit installiert.')
    return 0


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=['run', 'start', 'stop', 'status', 'install-systemd', 'uninstall-systemd'])
    parser.add_argument('--config', type=Path)
    parser.add_argument('--port', type=int, default=int(os.environ.get('PNH_PORT', DEFAULT_PORT)))
    parser.add_argument('--tick', type=int, default=int(os.environ.get('PNH_TICK_SECONDS', DEFAULT_TICK)))
    parser.add_argument('--managed', choices=['manual', 'systemd'], default='manual')
    parser.add_argument('--timeout', type=int, default=STOP_GRACE + 30)
    parser.add_argument('--python')
    parser.add_argument('--home')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args(argv)
    if not 5 <= args.tick <= 3600:
        parser.error('--tick muss zwischen 5 und 3600 Sekunden liegen')
    handler = {'run': cmd_run, 'start': cmd_start, 'stop': cmd_stop, 'status': cmd_status,
               'install-systemd': cmd_install_systemd, 'uninstall-systemd': cmd_uninstall_systemd}[args.command]
    return handler(Path(root).resolve(), args)


if __name__ == '__main__':
    raise SystemExit(main())
