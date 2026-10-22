#!/usr/bin/env python3
"""Render one standalone test segment with local TTS and FFmpeg."""
import argparse
import json
import subprocess
import tempfile
import textwrap
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
        from generate import synthesize
        if not (ROOT / "models/de_DE-thorsten-high.onnx").is_file():
            raise RuntimeError("Piper model missing; refuse eSpeak fallback in quality test")
        synthesize(segment["speech_text"], speech)
        if segment["kind"] == "story":
            from story_card import render
            picture = Path(directory) / "story-card.png"
            sources = segment.get("sources") or []
            publisher = sources[0].get("publisher", "RSS") if sources else "RSS"
            render(segment["headline"], publisher, int(args.segment.split("-")[-1]), picture)
        visual_input = (["-loop", "1", "-framerate", "25", "-i", str(picture)]
                        if picture.is_file() else
                        ["-f", "lavfi", "-i", "color=c=0x13243a:s=1280x720:r=25"])
        if not picture.is_file():
            print("Using generated fallback background:", picture)
        filters = "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p"
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", *visual_input, "-i", str(speech),
            "-vf", filters,
            "-c:v", "libx264", "-preset", "ultrafast", "-r", "25", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "48000", "-b:a", "160k", "-shortest", str(target)
        ], check=True)
    print("Rendered", args.segment, target.stat().st_size)
if __name__ == "__main__":
    main()
