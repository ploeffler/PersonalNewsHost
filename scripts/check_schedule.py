#!/usr/bin/env python3
"""Gate scheduled production according to public config; manual runs bypass gate."""
import datetime as dt
import json
import os
from pathlib import Path

config = json.loads((Path(__file__).resolve().parents[1] / "config.json").read_text(encoding="utf-8"))
settings = config.get("automation", {})
manual = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
enabled = settings.get("enabled", True)
interval = settings.get("interval_hours", 1)
start = settings.get("start_hour_utc", 0)
days = settings.get("days", "daily")
if type(interval) is not int or interval not in (1, 2, 3, 4, 6, 8, 12, 24):
    raise ValueError("automation.interval_hours must be 1,2,3,4,6,8,12,24")
if type(start) is not int or not 0 <= start <= 23:
    raise ValueError("automation.start_hour_utc must be between 0 and 23")
if days not in ("daily", "weekdays", "weekends"):
    raise ValueError("automation.days must be daily, weekdays or weekends")
now = dt.datetime.now(dt.timezone.utc)
day_allowed = days == "daily" or (days == "weekdays" and now.weekday() < 5) or (days == "weekends" and now.weekday() >= 5)
due = manual or (enabled and day_allowed and (now.hour - start) % interval == 0)
out = os.environ.get("GITHUB_OUTPUT")
if out:
    with open(out, "a", encoding="utf-8") as stream:
        stream.write("due=" + str(due).lower() + "\n")
print(f"Production {'enabled' if due else 'skipped'} at {now:%Y-%m-%d %H:%M} UTC (manual={manual}, interval={interval}h, start={start:02d}:00 UTC, days={days})")
