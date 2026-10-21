#!/usr/bin/env python3
"""Non-publishing CPU feasibility probe for an animated-presenter pipeline.

This does NOT implement AI lip sync. It measures the rendering budget and
checks whether a licensed portrait is available.
"""
import json
import os
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
presenter = cfg.get("presenter_settings", {})
portrait = root / presenter.get("portrait", "assets/presenter.png")
output = root / "avatar-test"
output.mkdir(exist_ok=True)
report = {"portrait_exists": portrait.is_file(), "cpu_count": os.cpu_count(),
          "lip_sync_implemented": False, "test_duration_seconds": 8}
audio = output / "test.wav"
if not portrait.is_file():
    raise SystemExit("Moderatorbild fehlt: Bitte assets/presenter.png ins Repository hochladen. Kein Testvideo ohne Gesicht.")
model = root / "models/de_DE-thorsten-high.onnx"
if not model.is_file():
    raise SystemExit("Piper-Stimmmodell fehlt; Test abgebrochen statt schlechterer Ersatzstimme.")
speech = "Guten Abend. Willkommen bei Personal News Host. Das ist ein Test."
subprocess.run(["piper", "--model", str(model), "--output_file", str(audio)],
               input=speech, text=True, check=True)
args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
if portrait.is_file():
    args += ["-loop", "1", "-framerate", "15", "-i", str(portrait),
             "-vf", "scale=640:360:force_original_aspect_ratio=decrease,"
                    "pad=640:360:(ow-iw)/2:(oh-ih)/2,format=yuv420p"]
else:
    args += ["-f", "lavfi", "-i", "color=c=0x13243a:s=640x360:r=15"]
args += ["-i", str(audio), "-t", "8", "-c:v", "libx264",
         "-preset", "veryfast", "-r", "15", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-shortest", str(output / "preview.mp4")]
started = time.monotonic()
subprocess.run(args, check=True, timeout=120)
report["render_wall_seconds"] = round(time.monotonic() - started, 2)
report["preview_bytes"] = (output / "preview.mp4").stat().st_size
report["note"] = "Static portrait preview only; no neural lip sync or mouth animation."
(output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
