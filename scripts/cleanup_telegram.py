#!/usr/bin/env python3
"""Delete bot messages no earlier than 25 hours after delivery."""
import datetime as dt
import json
import hashlib
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ledger = ROOT / "telegram_sent.json"
if not ledger.exists():
    print("No Telegram messages awaiting deletion.")
    raise SystemExit(0)
entries = json.loads(ledger.read_text(encoding="utf-8"))
if not entries:
    raise SystemExit(0)
token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
if not token:
    raise SystemExit("Telegram cleanup requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
now = dt.datetime.now(dt.timezone.utc)
remaining = []
for entry in entries:
    target = entry.get("target")
    if target not in ("default", "secondary") or not entry.get("chat_hash"):
        print("Skipping legacy entry without verified destination; manual migration required.")
        remaining.append(entry)
        continue
    chat_id = os.environ.get("TELEGRAM_CHAT_ID" if target == "default" else "TELEGRAM_CHAT_ID_SECONDARY", "").strip()
    if not chat_id or hashlib.sha256(chat_id.encode()).hexdigest() != entry["chat_hash"]:
        print("Destination missing or changed; retaining deletion entry.")
        remaining.append(entry)
        continue
    sent = dt.datetime.fromisoformat(entry["sent_at"])
    if now - sent < dt.timedelta(hours=25):
        remaining.append(entry)
        continue
    payload = urllib.parse.urlencode({"chat_id": chat_id, "message_id": entry["message_id"]}).encode()
    req = urllib.request.Request("https://api.telegram.org/bot" + token + "/deleteMessage", payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.load(response)
        if not result.get("ok"):
            raise RuntimeError("Telegram did not confirm deletion")
        print("Deleted Telegram message " + str(entry["message_id"]))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
        print("Telegram deletion failed for message " + str(entry["message_id"]) + ": " + str(exc).replace(token, "[REDACTED]"))
        remaining.append(entry)
ledger.write_text(json.dumps(remaining, indent=2) + "\n", encoding="utf-8")
