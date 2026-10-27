#!/usr/bin/env python3
"""Produce the newest due edition, including delayed or missed schedule runs."""
import datetime as dt
import email.utils
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

UTC = dt.timezone.utc


def latest_slot(settings, now):
    """Return the latest valid local-hour slot as UTC, once per DST hour."""
    interval = settings.get('interval_hours', 1)
    start = settings.get('start_hour_local', settings.get('start_hour_utc', 0))
    days = settings.get('days', 'daily')
    if type(interval) is not int or interval not in (1, 2, 3, 4, 6, 8, 12, 24):
        raise ValueError('automation.interval_hours must be 1,2,3,4,6,8,12,24')
    if type(start) is not int or not 0 <= start <= 23:
        raise ValueError('automation.start_hour_local must be between 0 and 23')
    if days not in ('daily', 'weekdays', 'weekends'):
        raise ValueError('automation.days must be daily, weekdays or weekends')
    zone = ZoneInfo(settings.get('timezone', 'UTC'))
    local = now.astimezone(zone)
    candidates = []
    for offset in range(8):
        date = local.date() - dt.timedelta(days=offset)
        if not day_allowed(days, date.weekday()):
            continue
        for hour in range(24):
            if (hour - start) % interval:
                continue
            wall = dt.datetime.combine(date, dt.time(hour), tzinfo=zone)
            instant = wall.astimezone(UTC)
            # A nonexistent spring hour does not become a later slot. fold=0
            # (the default above) selects the first repeated autumn hour only.
            if instant.astimezone(zone).replace(tzinfo=None) != wall.replace(tzinfo=None):
                continue
            if instant <= now:
                candidates.append(instant)
    return max(candidates) if candidates else None


def day_allowed(days, weekday):
    return days == 'daily' or (days == 'weekdays' and weekday < 5) or (days == 'weekends' and weekday >= 5)


def production_due(settings, now, published=None, manual=False):
    slot = latest_slot(settings, now)  # Validate even for manual/disabled runs.
    if manual:
        return True, slot, 'manual start'
    if not settings.get('enabled', True):
        return False, slot, 'automation disabled'
    local = now.astimezone(ZoneInfo(settings.get('timezone', 'UTC')))
    if not day_allowed(settings.get('days', 'daily'), local.weekday()):
        return False, slot, 'day excluded'
    if slot is None:
        return False, slot, 'no due slot'
    if published is not None and published <= now and published >= slot:
        return False, slot, 'latest due slot already published'
    return True, slot, 'latest due slot not yet published; produce one current edition'


def published_at(feed):
    """Use persisted publication data, never an attempted or failed run marker."""
    if not feed.exists():
        return None
    try:
        dates = []
        for item in ET.parse(feed).findall('./channel/item'):
            raw = item.findtext('pubDate')
            if raw:
                stamp = email.utils.parsedate_to_datetime(raw)
                if stamp.tzinfo is None:
                    raise ValueError('RSS publication date has no timezone')
                dates.append(stamp.astimezone(UTC))
        if not dates:
            raise ValueError('RSS contains no publication date')
        return max(dates)
    except (OSError, ET.ParseError, ValueError, TypeError, OverflowError):
        print('::warning::Publication date unavailable; next eligible run will produce one edition')
        return None


def main():
    try:
        from .provider_registry import require_executable_version
    except ImportError:
        from provider_registry import require_executable_version
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / 'config.json').read_text(encoding='utf-8'))
    require_executable_version(config)
    settings = config.get('automation', {})
    now = dt.datetime.now(UTC)
    published = published_at(root / 'docs/feed.xml')
    if published is not None and published > now:
        print('::warning::RSS publication date is in the future; ignoring it for scheduling')
    due, slot, reason = production_due(settings, now, published,
                                      os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch')
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a', encoding='utf-8') as stream:
            stream.write('due=' + str(due).lower() + '\n')
    local = now.astimezone(ZoneInfo(settings.get('timezone', 'UTC')))
    print(f"Production {'enabled' if due else 'skipped'} at {local:%Y-%m-%d %H:%M %Z}: {reason}; "
          f"latest_slot_utc={slot.isoformat() if slot else 'none'}; "
          f"published_utc={published.isoformat() if published else 'unknown'}")


if __name__ == '__main__':
    main()
