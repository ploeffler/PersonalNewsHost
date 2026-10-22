#!/usr/bin/env python3
"""Render one standalone test segment with local TTS and FFmpeg."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="broadcast-plan.json")
    parser.add_argument("--segment", required=True)
    parser.add_argument("--output-dir", default="rendered")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    segment = next((part for part in plan["segments"] if part["id"] == args.segment), None)
    if segment is None:
        raise ValueError("Unknown segment")
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    target = output / (args.segment + ".mp4")
    picture = ROOT / ("assets/presenter.png" if segment["presenter_visible"] else "assets/background.jpg")
    with tempfile.TemporaryDirectory() as directory:
        speech = Path(directory) / "speech.wav"
        subprocess.run(["espeak-ng", "-v", "de", "-s", "145", "-w", str(speech), segment["speech_text"]], check=True)
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "5",
            "-i", str(picture), "-i", str(speech),
            "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-r", "5",
            "-c:a", "aac", "-b:a", "96k", "-shortest", str(target)
        ], check=True)
    print("Rendered", args.segment, target.stat().st_size)
if __name__ == "__main__":
    main()
