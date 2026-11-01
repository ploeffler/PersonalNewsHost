#!/usr/bin/env python3
"""Repeatable user-owned Linux setup. Never installs OS packages or overwrites config."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT = '.venv-pnh'
MARKER = '.personalnewshost-managed'


class InstallError(RuntimeError):
    pass


def preflight(root=ROOT, os_info=None, machine=None, python_version=None, finder=None):
    root = Path(root)
    if os_info is None:
        try:os_info = platform.freedesktop_os_release()
        except OSError:os_info = {}
    machine = machine or platform.machine()
    python_version = python_version or tuple(sys.version_info[:2])
    finder = finder or shutil.which
    supported = os_info.get('ID') == 'ubuntu' and os_info.get('VERSION_ID') == '24.04' and machine in ('x86_64', 'amd64') and tuple(python_version) == (3, 12)
    missing = [name for name in ('git', 'ffmpeg', 'ffprobe', 'espeak-ng') if not finder(name)]
    files = [name for name in ('requirements.txt', 'requirements-constraints.txt', 'config.example.json') if not (root / name).is_file()]
    return {'platform': os_info.get('PRETTY_NAME', os_info.get('ID', 'unknown')), 'architecture': machine,
            'python': '.'.join(map(str, python_version)), 'validated_target': supported,
            'missing_commands': missing, 'missing_project_files': files,
            'ready': supported and not missing and not files,
            'os_package_hint': 'sudo apt-get install git python3-venv ffmpeg espeak-ng fonts-dejavu-core',
            'changes_system_packages': False, 'downloads_models': False}


def fingerprint(root):
    digest = hashlib.sha256()
    for name in ('requirements.txt', 'requirements-constraints.txt'):
        digest.update(name.encode());digest.update((root / name).read_bytes())
    digest.update(('Pillow;python=' + str(tuple(sys.version_info[:2]))).encode())
    return digest.hexdigest()


def install(root=ROOT, run=None):
    root = Path(root).resolve()
    run = run or subprocess.run
    report = preflight(root)
    if not report['ready']:
        raise InstallError('preflight_failed')
    env = root / ENVIRONMENT
    config = root / 'config.json'
    if env.is_symlink() or config.is_symlink():
        raise InstallError('symlink_install_target')
    if env.exists() and not (env / MARKER).is_file():
        raise InstallError('existing_environment_not_managed')
    created = not env.exists()
    if created:
        env.mkdir()
        (env / MARKER).write_text('PersonalNewsHost managed Python environment\n')
    python = env / 'bin/python'
    try:
        if not python.is_file():
            run([sys.executable, '-m', 'venv', str(env)], check=True, capture_output=True, text=True, timeout=120)
        identity = run([str(python), '-c', 'import json,sys; print(json.dumps({"prefix":sys.prefix,"version":list(sys.version_info[:2])}))'],
                       check=True, capture_output=True, text=True, timeout=20)
        actual = json.loads(identity.stdout)
        if Path(actual['prefix']).resolve() != env or actual['version'] != [3, 12]:
            raise InstallError('environment_identity_mismatch')
        stamp = env / '.requirements-sha256'
        wanted = fingerprint(root)
        reused = stamp.is_file() and stamp.read_text().strip() == wanted
        if reused:
            try:
                run([str(python), '-c', 'import jsonschema, PIL'], check=True, capture_output=True, text=True, timeout=20)
            except (OSError, subprocess.SubprocessError):
                reused = False
        if not reused:
            run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check',
                 '-c', str(root / 'requirements-constraints.txt'), '-r', str(root / 'requirements.txt'), 'Pillow'],
                check=True, capture_output=True, text=True, timeout=600)
        if not config.exists():
            descriptor = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write((root / 'config.example.json').read_bytes())
        run([str(python), str(root / 'scripts/validate_config.py'), str(config)],
            check=True, capture_output=True, text=True, timeout=30)
        stamp.write_text(wanted + '\n')
        for name in ('models', 'state/providers', 'state/install', 'out/productions', 'out/public', 'archive'):
            (root / name).mkdir(parents=True, exist_ok=True)
        result = {'status': 'installed', 'installed_at': time.time(), 'environment': str(env),
                  'reused_dependencies': reused, 'config_preserved': True,
                  'model_downloads': False, 'voice_baseline': 'system espeak-ng; optional Piper configured separately',
                  'platform': report, 'requirements_sha256': wanted}
        try:
            from .update_check import save
        except ImportError:
            from update_check import save
        save(root / 'state/install/install.json', result)
        return result
    except InstallError:
        raise
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        # pip output can include private registry/proxy details. Do not echo it.
        raise InstallError('environment_or_dependency_setup_failed') from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true', help='Create/update dedicated project environment')
    args = parser.parse_args(argv)
    try:
        result = install() if args.install else preflight()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if args.install or result['ready'] else 1
    except (InstallError, OSError, ValueError) as error:
        code = str(error) if isinstance(error, InstallError) else 'local_setup_failed'
        print('Linux installation stopped: ' + code, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
