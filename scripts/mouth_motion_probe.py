#!/usr/bin/env python3
"""Experimental audio-reactive mouth-motion preview, not phoneme-level lip sync."""
import json
import math
import subprocess
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

root = Path(__file__).resolve().parents[1]
cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
portrait = root / cfg["presenter_settings"].get("portrait", "assets/presenter.png")
out = root / "avatar-test"
out.mkdir(exist_ok=True)
audio = out / "test.wav"
if not portrait.is_file() or not audio.is_file():
    raise SystemExit("Missing presenter portrait or Piper test.wav; run avatar_probe.py first.")
image = Image.open(portrait).convert("RGB")
image.thumbnail((960, 540))
background = Image.new("RGB", (960, 540), "#13243a")
background.paste(image, ((960-image.width)//2, (540-image.height)//2))
with wave.open(str(audio)) as wav:
    rate = wav.getframerate()
    samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if wav.getnchannels() > 1:
        samples = samples.reshape(-1, wav.getnchannels()).mean(axis=1)
fps = 15
duration = min(8.0, len(samples) / rate)
settings = cfg.get("presenter_settings", {}).get("experimental_mouth", {})
cx = int(settings.get("center_x", 0.5083) * 960)
cy = int(settings.get("center_y", 0.3426) * 540)
width = int(settings.get("width", 0.048) * 960)
height = int(settings.get("max_open", 0.016) * 540)
# Calibration image uses exactly the same resized background as the video.
calibration = background.copy()
guide = ImageDraw.Draw(calibration)
for x in range(0, 961, 48):
    guide.line((x, 0, x, 539), fill=(100, 220, 220), width=1)
    if x < 960:
        guide.text((x + 2, 4), str(x), fill="white", stroke_width=1, stroke_fill="black")
for y in range(0, 541, 27):
    guide.line((0, y, 959, y), fill=(100, 220, 220), width=1)
    if y < 540:
        guide.text((4, y + 2), str(y), fill="white", stroke_width=1, stroke_fill="black")
guide.ellipse((cx-7, cy-7, cx+7, cy+7), outline="red", width=3)
guide.line((cx-18, cy, cx+18, cy), fill="red", width=3)
guide.line((cx, cy-18, cx, cy+18), fill="red", width=3)
guide.text((cx+15, cy+12), f"CURRENT {cx},{cy}", fill="red", stroke_width=1, stroke_fill="white")
calibration.save(out / "mouth-calibration.png")
print(f"Mouth calibration image: mouth-calibration.png, current position ({cx},{cy})")
frames = out / "mouth-frames"
frames.mkdir(exist_ok=True)
for n in range(max(1, math.ceil(duration * fps))):
    t = n / fps
    start = int(max(0, t-0.045) * rate)
    end = min(len(samples), int((t+0.045) * rate))
    level = float(np.sqrt(np.mean(samples[start:end] ** 2))) if end > start else 0.0
    opening = min(1.0, max(0.0, (level-0.012) * 14.0))
    frame = background.copy()
    if opening > 0.06:
        # Deform existing lower-lip pixels rather than drawing an oval on top.
        # The original lip seam stays fixed; lower lip/chin moves downward.
        displacement = max(1, int(round(height * opening)))
        x0, x1 = max(0, cx - width), min(frame.width, cx + width)
        y0, y1 = max(0, cy - 9), min(frame.height, cy + 29)
        patch = np.asarray(background.crop((x0, y0, x1, y1)), dtype=np.uint8)
        ph, pw = patch.shape[:2]
        yy, xx = np.mgrid[0:ph, 0:pw]
        # Taper deformation toward both corners and bottom of the patch.
        horizontal = np.maximum(0.0, 1.0 - ((xx - (cx-x0)) / max(1.0, width)) ** 2) ** 2
        vertical = np.clip((yy - (cy-y0) + 2) / 7.0, 0, 1) * np.clip((ph - yy) / 12.0, 0, 1)
        offset = displacement * horizontal * vertical
        source_y = np.clip(yy - offset, 0, ph - 1)
        low = np.floor(source_y).astype(int)
        high = np.minimum(low + 1, ph - 1)
        fraction = (source_y - low)[..., None]
        warped = (patch[low, xx] * (1 - fraction) + patch[high, xx] * fraction).astype(np.uint8)
        # Feather the warped patch into the original face.
        feather = (np.clip((xx + 1) / 9, 0, 1)
                   * np.clip((pw - xx) / 9, 0, 1)
                   * np.clip((yy + 1) / 6, 0, 1)
                   * np.clip((ph - yy) / 8, 0, 1))[..., None]
        blended = (warped * feather + patch * (1 - feather)).astype(np.uint8)
        frame.paste(Image.fromarray(blended), (x0, y0))
        # Narrow dark gap between original upper lip and displaced lower lip.
        layer = Image.new("RGBA", frame.size)
        draw = ImageDraw.Draw(layer)
        aperture = max(1, int(displacement * 0.65))
        draw.ellipse((cx-width//2, cy-1, cx+width//2, cy+aperture),
                     fill=(40, 18, 25, min(160, int(155 * opening))))
        layer = layer.filter(ImageFilter.GaussianBlur(0.8))
        frame = Image.alpha_composite(frame.convert("RGBA"), layer).convert("RGB")
    frame.save(frames / f"{n:04d}.jpg", quality=88)
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(fps),
                "-i", str(frames / "%04d.jpg"), "-i", str(audio), "-t", str(duration),
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-shortest", str(out / "mouth-motion-experimental.mp4")],
               check=True, timeout=120)
report = {"type": "experimental_lower_lip_pixel_deformation", "phoneme_lip_sync": False,
          "frames": math.ceil(duration * fps), "duration": duration,
          "mouth_position": [cx, cy], "note": "Audio-reactive lower-lip pixel warp with subtle artificial aperture; NOT phoneme-accurate neural lip sync."}
(out / "mouth-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
