#!/usr/bin/env python3
"""Optional Telegram delivery. Credentials are GitHub Actions secrets, never config.json."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def shorten(text, units):
    """Bound Telegram text conservatively by UTF-16 units, including emoji."""
    encoded = text.encode("utf-16-le")
    if len(encoded) <= units * 2:
        return text
    return encoded[:max(0, units - 1) * 2].decode("utf-16-le", errors="ignore") + "…"


def with_topics(caption):
    try:
        groups = json.loads((ROOT / "docs" / "story-groups.json").read_text(encoding="utf-8"))
        if not isinstance(groups, list):
            raise ValueError("Expected story list")
        topics = [" ".join(group["headline"].split()) for group in groups
                  if isinstance(group, dict) and isinstance(group.get("headline"), str)
                  and group["headline"].strip()]
    except (OSError, ValueError):
        print("Topic list unavailable; using configured Telegram caption.")
        topics = []
    if not topics:
        return shorten(caption, 1024)
    # Reserve room for the bulletin topics even with a long custom caption.
    caption = shorten(caption, 512)
    heading = "\n\nThemen:\n"
    budget = 1024 - len((caption + heading).encode("utf-16-le")) // 2
    per_topic = budget // len(topics) - 3  # bullet and line break
    if per_topic < 1:
        return shorten(caption + heading + "\n".join("• " + topic for topic in topics), 1024)
    return caption + heading + "\n".join("• " + shorten(topic, per_topic) for topic in topics)


cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
tg = cfg.get("telegram", {})
if not tg.get("enabled", False):
    print("Telegram disabled; skipping.")
    sys.exit(0)

token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
target = tg.get("target", "default")
if target not in ("default", "secondary"):
    sys.exit("Invalid telegram.target")
chat_id = os.environ.get("TELEGRAM_CHAT_ID" if target == "default" else "TELEGRAM_CHAT_ID_SECONDARY", "").strip()
if not token or not chat_id:
    print("Telegram enabled but TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.", file=sys.stderr)
    sys.exit(1)

video = ROOT / "docs" / "latest.mp4"
if not video.is_file() or video.stat().st_size == 0:
    sys.exit("Generated video missing or empty; refusing Telegram delivery")
delivery = tg.get("delivery", "auto")
if delivery not in ("auto", "video", "link"):
    sys.exit("Invalid telegram.delivery")
base = os.environ.get("PUBLIC_BASE_URL", "https://ploeffler.github.io/PersonalNewsHost/").rstrip("/") + "/"
url = base + "latest.mp4"
title = str(cfg.get("title", "PersonalNewsHost"))
caption = str(tg.get("caption", "{title} – neue Nachrichtensendung\n{url}")).replace("{title}", title).replace("{url}", url)
caption = with_topics(caption)
endpoint = "https://api.telegram.org/bot" + token + "/"
video = ROOT / "docs" / "latest.mp4"

def send(method, payload, video_file=None):
    if video_file:
        boundary = "----PersonalNewsHostTelegramBoundary"
        body = bytearray()
        for key, value in payload.items():
            body.extend(("--" + boundary + "\r\nContent-Disposition: form-data; name=\"" + key + "\"\r\n\r\n" + str(value) + "\r\n").encode())
        body.extend(("--" + boundary + "\r\nContent-Disposition: form-data; name=\"video\"; filename=\"latest.mp4\"\r\nContent-Type: video/mp4\r\n\r\n").encode())
        body.extend(video_file.read_bytes())
        body.extend(("\r\n--" + boundary + "--\r\n").encode())
        request = urllib.request.Request(endpoint + method, bytes(body), {"Content-Type": "multipart/form-data; boundary=" + boundary}, method="POST")
    else:
        data = urllib.parse.urlencode(payload).encode()
        request = urllib.request.Request(endpoint + method, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError("Telegram API returned an error")
    print("Telegram delivery succeeded: " + method)

payload = {"chat_id": chat_id}
if delivery != "link" and video.is_file() and video.stat().st_size <= 49 * 1024 * 1024:
    try:
        send("sendVideo", {**payload, "caption": caption}, video)
        sys.exit(0)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
        print("Video upload failed: " + str(exc).replace(token, "[REDACTED]"), file=sys.stderr)
        if delivery == "video" or not isinstance(exc, urllib.error.HTTPError) or exc.code not in (400, 413):
            # Timeouts may mean Telegram accepted the upload: avoid duplicate posts.
            sys.exit(1)
elif delivery == "video":
    sys.exit("Video missing or too large for direct Telegram delivery")
try:
    send("sendMessage", {**payload, "text": caption})
except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
    print("Telegram link delivery failed: " + str(exc).replace(token, "[REDACTED]"), file=sys.stderr)
    sys.exit(1)
