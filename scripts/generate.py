#!/usr/bin/env python3
"""Zero-cost RSS -> narrated static-image video -> podcast-style video RSS."""
import datetime as dt
import email.utils
import html
import json
import re
import subprocess
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
BASE = "https://ploeffler.github.io/PersonalNewsHost/"
UA = "PersonalNewsHost/0.4-scenes (RSS news reader)"
ATOM = "{http://www.w3.org/2005/Atom}"

def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def fetch(url):
    if not url.startswith(("https://", "http://")):
        raise ValueError("Only HTTP(S) RSS URLs allowed")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=12) as resp:
        return resp.read(1_500_000)

def items_from_feed(url):
    root = ET.fromstring(fetch(url))
    result = []
    for node in root.findall(".//item")[:15]:
        title = clean(node.findtext("title"))
        desc = clean(node.findtext("description"))
        link = clean(node.findtext("link"))
        if title:
            result.append((title, desc, link))
    if not result:
        for node in root.findall(".//" + ATOM + "entry")[:15]:
            title = clean(node.findtext(ATOM + "title"))
            summary = clean(node.findtext(ATOM + "summary") or node.findtext(ATOM + "content"))
            link_node = node.find(ATOM + "link")
            link = link_node.get("href", "") if link_node is not None else ""
            if title:
                result.append((title, summary, link))
    return result

def run(args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)

def adjust_voice_pitch(wav):
    """Lower or raise voice pitch with FFmpeg while preserving speech duration."""
    import math
    import wave
    semitones = float(CONFIG.get("voice_pitch_semitones", 0))
    if not math.isfinite(semitones) or not -6 <= semitones <= 6:
        raise ValueError("voice_pitch_semitones must be between -6 and 6")
    if abs(semitones) < 0.01:
        return
    with wave.open(str(wav), "rb") as audio:
        rate = audio.getframerate()
    factor = 2 ** (semitones / 12)
    target = Path(wav).with_name(Path(wav).stem + "-pitch.wav")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
            "-af", f"asetrate={rate}*{factor:.8f},aresample={rate},atempo={1/factor:.8f}",
            "-ar", str(rate), "-c:a", "pcm_s16le", str(target)
        ], check=True)
        target.replace(wav)
        print(f"Voice pitch adjusted: {semitones:+.1f} semitones (tempo preserved)")
    finally:
        target.unlink(missing_ok=True)

def synthesize(script, wav):
    """Use local Piper neural TTS if available; retain eSpeak as safe fallback."""
    import os
    model = ROOT / "models" / "de_DE-thorsten-high.onnx"
    if model.is_file():
        try:
            subprocess.run(
                ["piper", "--model", str(model), "--length_scale", str(CONFIG.get("piper_length_scale", 1.13)), "--sentence_silence", "0.38", "--output_file", str(wav)],
                input=script, text=True, check=True, timeout=180,
                stdout=subprocess.DEVNULL
            )
            if wav.is_file() and wav.stat().st_size > 44:
                print("Speech engine: Piper (de_DE-thorsten-high)")
                adjust_voice_pitch(wav)
                return
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"Piper failed; falling back to eSpeak-NG: {exc}")
    run(["espeak-ng", "-v", CONFIG.get("voice", "de"), "-s", "145", "-w", str(wav), script])
    print("Speech engine: eSpeak-NG fallback")
    adjust_voice_pitch(wav)

def main():
    DOCS.mkdir(exist_ok=True)
    collected, seen = [], set()
    for url in CONFIG["feeds"]:
        try:
            for title, desc, link in items_from_feed(url):
                key = title.casefold()
                if key not in seen:
                    seen.add(key)
                    collected.append((title, desc, link))
        except Exception as exc:
            print(f"Feed skipped: {url}: {exc}")
    if not collected:
        raise RuntimeError("No RSS entries available; previous published edition remains unchanged")
    selected = collected[:max(1, min(int(CONFIG.get("max_items", 5)), 10))]
    now = dt.datetime.now(dt.timezone.utc)
    timestamp = now.strftime("%d.%m.%Y um %H:%M UTC")
    settings = CONFIG.get("presenter_settings", {})
    scenes = settings.get("scenes", {})
    moderator = str(settings.get("name") or "NewsHost")
    def expand_scene_text(value):
        return str(value).replace("{title}", str(CONFIG["title"])).replace("{moderator}", moderator)
    intro_text = expand_scene_text(scenes.get("intro_text") or "Willkommen bei {title}. Hier sind die Nachrichten.")
    outro_text = expand_scene_text(scenes.get("outro_text") or "Das waren die Schlagzeilen. Quellen und Links finden Sie auf unserer Webseite.")
    parts = [intro_text, f"Die Nachrichten vom {timestamp}."]
    limit = max(0, min(int(CONFIG.get("max_description_chars", 180)), 300))
    for title, desc, _ in selected:
        parts.append(title.rstrip(".!?") + ".\n" + (desc[:limit].rsplit(" ", 1)[0] if len(desc) > limit else desc))
    parts.append(outro_text)
    script = "\n\n".join(parts)
    (DOCS / "transcript.txt").write_text(script + "\n", encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "speech.wav"
        synthesize(script, wav)
        settings = CONFIG.get("presenter_settings", {})
        bg = ROOT / settings.get("background", CONFIG.get("background", "assets/background.jpg"))
        presenter = ROOT / settings.get("portrait", CONFIG.get("presenter", "assets/presenter.png"))
        if settings.get("lip_sync", {}).get("enabled", False):
            print("Lip sync requested but no validated engine is installed; using static portrait fallback")
        # Scene schedule: presenter for intro/outro, headlines in the middle.
        duration_text = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(wav)], text=True
        ).strip()
        duration = float(duration_text)
        scenes = settings.get("scenes", {})
        intro = max(0.0, min(float(scenes.get("intro_seconds", 8)), duration / 3))
        outro = max(0.0, min(float(scenes.get("outro_seconds", 8)), duration / 3))
        outro_start = max(intro, duration - outro)
        print(f"Scenes: intro={intro:.1f}s, headlines={outro_start-intro:.1f}s, outro={outro:.1f}s")
        args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        if bg.is_file():
            args += ["-loop", "1", "-i", str(bg)]
        else:
            args += ["-f", "lavfi", "-i", "color=c=0x13243a:s=1280x720:r=1"]
        args += ["-i", str(wav)]
        filters = ["[0:v]fps=5,scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p,setpts=PTS-STARTPTS[bg]"]
        current = "bg"
        if presenter.is_file():
            args += ["-loop", "1", "-i", str(presenter)]
            filters += [
                "[2:v]scale=440:600:force_original_aspect_ratio=decrease[person]",
                f"[{current}][person]overlay=x=W-w-55:y=H-h-30:"
                f"enable='between(t,0,{intro:.3f})+gte(t,{outro_start:.3f})'[composed]"
            ]
            current = "composed"
        if scenes.get("show_headlines", True) and selected:
            # Each headline gets its own timed overlay, rather than one overflowing text block.
            story_count = len(selected)
            story_duration = max(0.0, outro_start - intro) / story_count
            for idx, (title, _, _) in enumerate(selected):
                start_time = intro + idx * story_duration
                end_time = intro + (idx + 1) * story_duration
                headline_file = Path(tmp) / f"headline_{idx}.txt"
                # Wrap text to fit the 1280px canvas.
                import textwrap
                headline_file.write_text(
                    "\n".join(textwrap.wrap(title, width=42, break_long_words=True)),
                    encoding="utf-8"
                )
                print(f"Headline {idx+1}/{story_count}: {start_time:.1f}-{end_time:.1f}s: {title[:65]}")
                next_label = "v" if idx == story_count - 1 else f"story{idx}"
                filters.append(
                    f"[{current}]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                    f"textfile={headline_file}:fontcolor=white:fontsize=38:line_spacing=15:"
                    f"x=70:y=(h-text_h)/2:box=1:boxcolor=0x091a2acc:boxborderw=24:"
                    f"enable='gte(t,{start_time:.3f})*lt(t,{end_time:.3f})'[{next_label}]"
                )
                current = next_label
        else:
            filters.append(f"[{current}]null[v]")
        args += ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", "1:a",
                 "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
                 "-r", "5", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                 "-shortest", "-movflags", "+faststart", str(DOCS / "latest.mp4")]
        run(args)
    lines = ["<!doctype html><html lang='de'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>PersonalNewsHost</title><style>body{font:1.1rem system-ui;background:#13243a;color:white;max-width:900px;margin:3rem auto;padding:1rem}a{color:#8ed6ff}video{width:100%}</style>",
             "<h1>PersonalNewsHost</h1><p>Stand: " + html.escape(timestamp) + "</p>",
             "<video controls src='latest.mp4?v=" + now.strftime("%Y%m%d%H%M%S") + "'></video><p><a href='feed.xml'>Video-RSS abonnieren</a> · <a href='transcript.txt'>Transkript</a> · <a href='settings.html'>Konfiguration (Beta)</a></p><h2>Quellen</h2><ul>"]
    for title, _, link in selected:
        safe = link if link.startswith(("https://", "http://")) else "#"
        lines.append("<li><a rel='noopener noreferrer' href='" + html.escape(safe, quote=True) + "'>" + html.escape(title) + "</a></li>")
    lines.append("</ul><p>Automatisch aus RSS erstellt; Inhalte nicht unabhängig überprüft.</p></html>")
    (DOCS / "index.html").write_text("\n".join(lines), encoding="utf-8")
    pubdate = email.utils.format_datetime(now)
    guid = now.isoformat()
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
            '<title>PersonalNewsHost Videos</title><link>' + BASE + '</link>'
            '<description>Automatisch generierte Nachrichten-Videos</description><language>de</language>'
            '<atom:link href="' + BASE + 'feed.xml" rel="self" type="application/rss+xml"/>'
            '<item><title>Nachrichten ' + html.escape(timestamp) + '</title>'
            '<guid isPermaLink="false">' + guid + '</guid>'
            '<pubDate>' + pubdate + '</pubDate>'
            '<description>Aktuelle Ausgabe; Quellen auf der Webseite.</description>'
            '<enclosure url="' + BASE + 'latest.mp4" length="' + str((DOCS / "latest.mp4").stat().st_size) + '" type="video/mp4"/>'
            '</item></channel></rss>')
    (DOCS / "feed.xml").write_text(feed, encoding="utf-8")
    print(f"Generated {len(selected)} stories; video size {(DOCS / 'latest.mp4').stat().st_size} bytes")

if __name__ == "__main__":
    main()
