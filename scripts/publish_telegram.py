#!/usr/bin/env python3
"""Optional Telegram delivery. Credentials are GitHub Actions secrets, never config.json."""
import json
import datetime as dt
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
# Read before sending: corrupt state must never silently erase pending deletions.
ledger = ROOT / "telegram_sent.json"
entries = json.loads(ledger.read_text(encoding="utf-8")) if ledger.exists() else []
if not isinstance(entries, list):
    sys.exit("Invalid Telegram deletion ledger")

delivery = tg.get("delivery", "auto")
if delivery not in ("auto", "video", "link"):
    sys.exit("Invalid telegram.delivery")
base = os.environ.get("PUBLIC_BASE_URL", "https://ploeffler.github.io/PersonalNewsHost/").rstrip("/") + "/"
url = base + "latest.mp4"
title = str(cfg.get("title", "PersonalNewsHost"))
caption = str(tg.get("caption", "{title} – neue Nachrichtensendung\n{url}")).replace("{title}", title).replace("{url}", url)
caption = caption[:1024]
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
    message_id = result.get("result", {}).get("message_id")
    if tg.get("auto_delete", True):
        if message_id is None:
            raise RuntimeError("Telegram response missing message_id")
        import hashlib
        entries.append({"message_id": message_id, "target": target,
                        "chat_hash": hashlib.sha256(chat_id.encode()).hexdigest(),
                        "sent_at": dt.datetime.now(dt.timezone.utc).isoformat()})
        temporary = ledger.with_suffix(".tmp")
        temporary.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
        temporary.replace(ledger)

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
