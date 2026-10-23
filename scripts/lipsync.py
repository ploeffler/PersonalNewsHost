#!/usr/bin/env python3
"""Lightweight offline, audio-driven mouth animation for a transparent presenter PNG.

This is an amplitude-driven approximation, not phoneme-accurate neural lip sync.
The mouth position is configurable because arbitrary portrait layouts differ.
"""
import math
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

def generate_frames(portrait, wav_path, output_dir, fps=5, mouth=None):
    mouth = mouth or {"x": 0.5, "y": 0.34, "width": 0.13, "height": 0.045}
    img = Image.open(portrait).convert("RGBA")
    # Match the on-screen dimensions to avoid processing full-resolution frames.
    img.thumbnail((530, 665), Image.Resampling.LANCZOS)
    w, h = img.size
    mx = int(w * float(mouth.get("x", 0.5)))
    my = int(h * float(mouth.get("y", 0.34)))
    mw = max(10, int(w * float(mouth.get("width", 0.13))))
    mh = max(6, int(h * float(mouth.get("height", 0.045))))
    if not (mw < w // 2 and mh < h // 5 and mw // 2 < mx < w - mw // 2 and mh < my < h - mh):
        raise ValueError("Invalid mouth rectangle; configure lip_sync.mouth")
    left, top, right, bottom = mx - mw // 2, my - mh, mx + mw // 2, my + mh
    original = img.crop((left, top, right, bottom))
    # Feather the localized deformation to preserve facial identity.
    mask = Image.new("L", (right - left, bottom - top), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((3, 2, mask.width - 3, mask.height - 2), fill=220)
    mask = mask.filter(ImageFilter.GaussianBlur(max(2, mh // 3)))
    with wave.open(str(wav_path), "rb") as audio:
        rate = audio.getframerate()
        channels = audio.getnchannels()
        width = audio.getsampwidth()
        if width != 2:
            raise ValueError("Lip sync expects 16-bit PCM WAV")
        frames = audio.readframes(audio.getnframes())
    import array
    samples = array.array("h")
    samples.frombytes(frames)
    count = len(samples) // channels
    total = math.ceil(count / rate * fps)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    # A smoothed speech-energy envelope drives mouth aperture.
    energy = []
    for i in range(total):
        center = int((i + 0.5) * rate / fps)
        start = max(0, center - rate // 16)
        end = min(count, center + rate // 16)
        stride = max(1, (end - start) // 1500)
        values = (samples[j * channels] for j in range(start, end, stride))
        v = list(values)
        rms = math.sqrt(sum(x * x for x in v) / max(1, len(v))) / 32768
        energy.append(rms)
    peak = max(sorted(energy)[int(len(energy) * .85)] if energy else 0, 0.012)
    previous = 0.0
    for i, rms in enumerate(energy):
        target = max(0, min(1, (rms / peak - 0.16) / 0.95))
        previous = 0.55 * previous + 0.45 * target
        opening = previous
        frame = img.copy()
        if opening > 0.05:
            # Stretch the lip region around its midpoint; keep a smooth boundary.
            scale = 1.0 + opening * 0.42
            new_h = max(2, round(original.height * scale))
            stretched = original.resize((original.width, new_h), Image.Resampling.BICUBIC)
            patch = Image.new("RGBA", original.size, (0, 0, 0, 0))
            patch.paste(stretched, (0, (original.height - new_h) // 2))
            frame.paste(patch, (left, top), mask)
        frame.save(output_dir / f"lip_{i:06d}.png", compress_level=1)
    return total
