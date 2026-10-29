#!/usr/bin/env python3
"""Install two isolated, version-pinned CPU runtimes for the experimental reel.

The legacy avatar stack requires different NumPy/Torch versions than the image
stack. Dedicated requirements are intentional; no production environment changes.
"""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SADTALKER_REVISION = 'cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8'


def main():
    env = dict(os.environ)
    env.pop('PIP_CONSTRAINT', None)  # Each isolated stack has its own exact pins.
    for name, torch_version, vision_version, requirements in [
        ('image', '2.8.0+cpu', '0.23.0+cpu', 'requirements-reel-image.txt'),
        ('avatar', '1.13.1+cpu', '0.14.1+cpu', 'requirements-reel-avatar.txt'),
    ]:
        venv = ROOT / ('.reel-' + name)
        subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
        python = str(venv / 'bin/python')
        subprocess.run([python, '-m', 'pip', 'install', 'pip==24.3.1', 'setuptools==69.5.1', 'wheel==0.45.1'], env=env, check=True)
        subprocess.run([python, '-m', 'pip', 'install', '--index-url', 'https://download.pytorch.org/whl/cpu',
                        'torch==' + torch_version, 'torchvision==' + vision_version], env=env, check=True)
        subprocess.run([python, '-m', 'pip', 'install', '-r', str(ROOT / requirements)], env=env, check=True)
    source = ROOT / '.reel-models/SadTalker'
    source.parent.mkdir(exist_ok=True)
    subprocess.run(['git', 'clone', '--no-checkout', 'https://github.com/OpenTalker/SadTalker.git', str(source)], check=True)
    subprocess.run(['git', '-C', str(source), 'checkout', SADTALKER_REVISION], check=True)


if __name__ == '__main__':
    main()
