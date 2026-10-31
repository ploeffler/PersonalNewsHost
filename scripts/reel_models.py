#!/usr/bin/env python3
"""Generate fictional presenter/studio with SD-Turbo; run real SadTalker on CPU."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request

IMAGE_MODEL = 'stabilityai/sd-turbo'
IMAGE_REVISION = 'b261bac6fd2cf515557d5d0707481eafa0485ec2'


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.stat().st_size > 1000:
        return
    with urllib.request.urlopen(url, timeout=120) as response, path.with_suffix(path.suffix + '.part').open('wb') as output:
        shutil.copyfileobj(response, output)
    path.with_suffix(path.suffix + '.part').replace(path)


def images(args):
    import torch
    from diffusers import AutoPipelineForText2Image
    torch.set_num_threads(min(4, os.cpu_count() or 2))
    print('Loading pinned SD-Turbo FP16 downloads for float32 CPU inference', flush=True)
    pipe = AutoPipelineForText2Image.from_pretrained(IMAGE_MODEL, revision=IMAGE_REVISION, variant='fp16', torch_dtype=torch.float32,
                                                   use_safetensors=True)
    pipe.to('cpu')
    pipe.enable_attention_slicing()
    pipe.enable_vae_slicing()
    prompts = [
        ('host.png', 'Studio headshot of one fictional adult news presenter, face centered, facing camera, head and shoulders, visible face, eyes open, mouth relaxed, plain neutral background. ' + args.host),
        ('studio.png', 'Professional television news studio background, no people, no text, empty presenter position, portrait composition. ' + args.studio),
    ]
    for index, (filename, prompt) in enumerate(prompts):
        print('Generating ' + filename, flush=True)
        image = pipe(prompt=prompt[:1500], num_inference_steps=2, guidance_scale=0.0,
                     generator=torch.Generator(device='cpu').manual_seed(3407 + index)).images[0]
        image.save(args.work / filename)
        print('Saved ' + filename, flush=True)


def animate(args):
    source = args.source.resolve()
    release = 'https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/'
    for name in ['SadTalker_V0.0.2_256.safetensors', 'mapping_00229-model.pth.tar']:
        download(release + name, source / 'checkpoints' / name)
    for name in ['alignment_WFLW_4HG.pth', 'detection_Resnet50_Final.pth']:
        download('https://github.com/xinntao/facexlib/releases/download/v0.1.0/' + name, source / 'gfpgan/weights' / name)
    result = args.work.resolve() / 'avatar'
    result.mkdir(exist_ok=True)
    env = dict(os.environ, OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', CUDA_VISIBLE_DEVICES='')
    # Resolving the venv's Python symlink selects the base interpreter and loses
    # its installed packages. Make the path absolute without following symlinks.
    subprocess.run([str(args.python.absolute()), str(source / 'inference.py'), '--cpu', '--still', '--size', '256',
                    '--batch_size', '1', '--preprocess', 'crop', '--source_image', str((args.work / 'host.png').resolve()),
                    '--driven_audio', str((args.work / 'speech.wav').resolve()), '--result_dir', str(result)],
                   cwd=source, env=env, check=True, timeout=2400)
    videos = sorted(result.glob('*.mp4'))
    if not videos:
        raise RuntimeError('Avatar inference produced no video; no static fallback is substituted')
    shutil.copyfile(videos[-1], args.work / 'talking-host.mp4')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['images', 'animate'])
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--host', default='')
    p.add_argument('--studio', default='')
    p.add_argument('--source', type=Path)
    p.add_argument('--python', type=Path)
    a = p.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)
    (images if a.stage == 'images' else animate)(a)


if __name__ == '__main__':main()
