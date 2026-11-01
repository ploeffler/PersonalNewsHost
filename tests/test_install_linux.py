"""T181: isolated setup, safe repetition and refusal of unmanaged environments."""
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts import install_linux as installer


class LinuxInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('requirements.txt', 'requirements-constraints.txt'):(self.root/name).write_text('fixture==1\n')
        (self.root/'config.example.json').write_text('{"title":"Default"}')
        self.calls = []

    def ready(self):
        return installer.preflight(self.root, {'ID':'ubuntu','VERSION_ID':'24.04'}, 'x86_64', (3,12), lambda name: '/bin/'+name)

    def fake_run(self, args, **kwargs):
        self.calls.append(args)
        env = self.root / installer.ENVIRONMENT
        if args[1:3] == ['-m','venv']:
            (env/'bin').mkdir(exist_ok=True);(env/'bin/python').write_text('fixture')
        return SimpleNamespace(stdout=json.dumps({'prefix':str(env),'version':[3,12]}), returncode=0)

    def perform(self):
        with patch.object(installer, 'preflight', return_value=self.ready()):return installer.install(self.root, self.fake_run)

    def test_platform_and_prerequisite_checks_are_read_only(self):
        self.assertTrue(self.ready()['ready'])
        result=installer.preflight(self.root,{'ID':'ubuntu','VERSION_ID':'26.04'},'x86_64',(3,14),lambda name:None)
        self.assertFalse(result['ready']);self.assertIn('espeak-ng',result['missing_commands'])
        self.assertFalse((self.root/installer.ENVIRONMENT).exists())

    def test_repeated_install_preserves_config_secrets_models_archive_and_skips_pip(self):
        protected={'config.json':b'private-config','state/private-key':b'private-value','models/existing.onnx':b'weights','archive/edition.mp4':b'video'}
        for name,data in protected.items():
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        first=self.perform();self.calls.clear();second=self.perform()
        self.assertFalse(first['reused_dependencies']);self.assertTrue(second['reused_dependencies'])
        self.assertFalse(any('pip' in args for args in self.calls))
        for name,data in protected.items():self.assertEqual((self.root/name).read_bytes(),data)

    def test_config_seed_only_when_absent(self):
        self.perform()
        self.assertEqual((self.root/'config.json').read_bytes(),(self.root/'config.example.json').read_bytes())

    def test_unknown_environment_and_symlink_are_not_modified(self):
        env=self.root/installer.ENVIRONMENT;env.mkdir();(env/'keep').write_text('existing')
        with self.assertRaises(installer.InstallError):self.perform()
        self.assertEqual((env/'keep').read_text(),'existing');self.assertEqual(self.calls,[])
        (env/'keep').unlink();env.rmdir();env.symlink_to(self.root)
        with self.assertRaises(installer.InstallError):self.perform()
        self.assertEqual(self.calls,[])

    def test_failed_setup_can_retry_without_discarding_owned_environment(self):
        def failed(*args,**kwargs):raise subprocess.CalledProcessError(1,args[0],stderr='private-proxy-key')
        with patch.object(installer,'preflight',return_value=self.ready()),self.assertRaises(installer.InstallError) as error:
            installer.install(self.root,failed)
        self.assertNotIn('private-proxy-key',str(error.exception))
        self.assertTrue((self.root/installer.ENVIRONMENT/installer.MARKER).exists())
        self.assertEqual(self.perform()['status'],'installed')

    def test_changed_requirements_refresh_only_managed_dependencies(self):
        self.perform();self.calls.clear();(self.root/'requirements.txt').write_text('fixture==2\n')
        self.assertFalse(self.perform()['reused_dependencies'])
        self.assertTrue(any('pip' in args for args in self.calls))
