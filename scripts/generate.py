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
UA = "PersonalNewsHost/0.2 (RSS news reader)"
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

def synthesize(script, wav):
    """Use local Piper neural TTS if available; retain eSpeak as safe fallback."""
    import os
    model = ROOT / "models" / "de_DE-thorsten-medium.onnx"
    if model.is_file():
        try:
            subprocess.run(
                ["piper", "--model", str(model), "--output_file", str(wav)],
                input=script, text=True, check=True, timeout=180,
                stdout=subprocess.DEVNULL
            )
            if wav.is_file() and wav.stat().st_size > 44:
                print("Speech engine: Piper (de_DE-thorsten-medium)")
                return
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"Piper failed; falling back to eSpeak-NG: {exc}")
    run(["espeak-ng", "-v", CONFIG.get("voice", "de"), "-s", "145", "-w", str(wav), script])
    print("Speech engine: eSpeak-NG fallback")

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
    parts = [f"Willkommen bei {CONFIG['title']}. Die Nachrichten vom {timestamp}."]
    limit = max(0, min(int(CONFIG.get("max_description_chars", 180)), 300))
    for title, desc, _ in selected:
        parts.append(title + ". " + (desc[:limit].rsplit(" ", 1)[0] if len(desc) > limit else desc))
    parts.append("Das waren die Schlagzeilen. Quellen und Links finden Sie auf unserer Webseite.")
    script = "\n\n".join(parts)
    (DOCS / "transcript.txt").write_text(script + "\n", encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "speech.wav"
        synthesize(script, wav)
        bg = ROOT / CONFIG.get("background", "assets/background.jpg")
        presenter = ROOT / CONFIG.get("presenter", "assets/presenter.png")
        filters = []
        args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        if bg.is_file():
            args += ["-loop", "1", "-i", str(bg)]
        else:
            args += ["-f", "lavfi", "-i", "color=c=0x13243a:s=1280x720:r=1"]
        args += ["-i", str(wav)]
        if presenter.is_file():
            args += ["-loop", "1", "-i", str(presenter)]
            filters = ["[0:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720[bg]",
                       "[2:v]scale=440:600:force_original_aspect_ratio=decrease[person]",
                       "[bg][person]overlay=W-w-55:H-h-30,format=yuv420p[v]"]
        else:
            filters = ["[0:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,format=yuv420p[v]"]
        args += ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", "1:a",
                 "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
                 "-r", "1", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
                 "-shortest", "-movflags", "+faststart", str(DOCS / "latest.mp4")]
        run(args)
    lines = ["<!doctype html><html lang='de'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>PersonalNewsHost</title><style>body{font:1.1rem system-ui;background:#13243a;color:white;max-width:900px;margin:3rem auto;padding:1rem}a{color:#8ed6ff}video{width:100%}</style>",
             "<h1>PersonalNewsHost</h1><p>Stand: " + html.escape(timestamp) + "</p>",
             "<video controls src='latest.mp4'></video><p><a href='feed.xml'>Video-RSS abonnieren</a> · <a href='transcript.txt'>Transkript</a></p><h2>Quellen</h2><ul>"]
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
