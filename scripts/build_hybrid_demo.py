#!/usr/bin/env python3
"""Experimental MuseTalk intro + existing bulletin. Does not alter docs/ production."""
import json
import subprocess
from pathlib import Path

def run(*args):
    subprocess.run(args, check=True)

def probe(path):
    return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(path)],text=True))["format"]["duration"])

def main():
    folder=Path("musetalk-hybrid-interpolation")
    intro=folder/"official-speaking-presenter.mp4"
    news=Path("docs/latest.mp4")
    target=folder/"hybrid-news-demo.mp4"
    if not intro.is_file() or not news.is_file():
        raise SystemExit("Missing intro or published bulletin; cannot create hybrid demo")
    # Normalize to 1280x720, 25 fps, and concatenate independent A/V segments.
    # The first five seconds retain the test speech because they were conditioned on it.
    # The following segment retains the original news soundtrack; this is NOT a
    # production-ready lip-synced intro to the actual bulletin.
    graph=(
        "[0:v]fps=25,scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,"
        "trim=duration=5,setpts=PTS-STARTPTS[v0];"
        "[0:a]aresample=48000,atrim=duration=5,asetpts=PTS-STARTPTS[a0];"
        "[1:v]fps=25,scale=1280:720:force_original_aspect_ratio=decrease,"
        "pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,"
        "setpts=PTS-STARTPTS[v1];"
        "[1:a]aresample=48000,asetpts=PTS-STARTPTS[a1];"
        "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
    )
    run("ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(intro),"-i",str(news),
        "-filter_complex",graph,"-map","[v]","-map","[a]",
        "-c:v","libx264","-preset","veryfast","-crf","27","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","96k","-movflags","+faststart",str(target))
    report={"status":"success","mode":"experimental intro + current published news",
        "intro_duration_seconds":float(probe(intro)),"news_duration_seconds":float(probe(news)),
        "demo_duration_seconds":float(probe(target)),
        "warning":"Intro uses benchmark speech, not the news intro; NOT production lip sync.",
        "output":str(target)}
    (folder/"integration-report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
