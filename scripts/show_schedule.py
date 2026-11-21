#!/usr/bin/env python3
"""Show planning and GitHub Actions minute budget (T070).

``budget``  estimates monthly Actions minutes from the cron triggers in
            .github/workflows, measured run times (planning/workflow-minutes.json)
            and the publication schedule in the configuration.
``crontab`` prints one cron trigger per show for local production with
            produce_show.py. Each show has its own lock (a show never overlaps
            itself) and all shows share a render lock (one render at a time).
"""
import argparse
import datetime as dt
import json
import math
import shlex
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTH_DAYS = 30
INTERVALS = (1, 2, 3, 4, 6, 8, 12, 24)


def _field(spec, low, high):
    values = set()
    for part in spec.split(','):
        step = 1
        if '/' in part:
            part, raw = part.split('/', 1)
            step = int(raw)
            if step < 1:
                raise ValueError('cron step must be positive')
        if part == '*':
            start, end = low, high
        elif '-' in part:
            start, end = (int(x) for x in part.split('-', 1))
        else:
            start = int(part)
            end = high if step > 1 else start
        if not low <= start <= end <= high:
            raise ValueError(f'cron value out of range: {spec}')
        values.update(range(start, end + 1, step))
    return values


def parse_cron(expression):
    """Five-field cron (UTC, as GitHub Actions uses it) into sets of allowed values."""
    fields = expression.split()
    if len(fields) != 5:
        raise ValueError('cron needs five fields')
    minute, hour, day, month, weekday = fields
    weekdays = {0 if d == 7 else d for d in _field(weekday, 0, 7)}
    return {'minute': _field(minute, 0, 59), 'hour': _field(hour, 0, 23), 'day': _field(day, 1, 31),
            'month': _field(month, 1, 12), 'weekday': weekdays,
            'any_day': day == '*', 'any_weekday': weekday == '*'}


def cron_matches(cron, moment):
    if moment.minute not in cron['minute'] or moment.hour not in cron['hour'] or moment.month not in cron['month']:
        return False
    day_ok = moment.day in cron['day']
    weekday_ok = (moment.weekday() + 1) % 7 in cron['weekday']
    if cron['any_day'] or cron['any_weekday']:
        return day_ok and weekday_ok
    return day_ok or weekday_ok  # classic cron: either restricted field may match


def runs_per_month(expression, days=MONTH_DAYS, start=dt.datetime(2026, 1, 5)):
    cron = parse_cron(expression)
    count, moment, end = 0, start, start + dt.timedelta(days=days)
    while moment < end:
        if moment.hour in cron['hour'] and moment.minute == 0:
            count += sum(1 for minute in cron['minute'] if cron_matches(cron, moment.replace(minute=minute)))
        moment += dt.timedelta(hours=1)
    return count


def editions_per_month(automation, days=MONTH_DAYS):
    """Scheduled editions per month from interval_hours/days (local time)."""
    if not automation.get('enabled', True):
        return 0
    interval = automation.get('interval_hours', 1)
    if interval not in INTERVALS:
        raise ValueError('automation.interval_hours must be 1,2,3,4,6,8,12,24')
    share = {'daily': 1, 'weekdays': 5 / 7, 'weekends': 2 / 7}[automation.get('days', 'daily')]
    return round(24 // interval * days * share)


def workflow_info(path):
    """Triggers, concurrency and job timeouts; a small line parser, no YAML dependency."""
    text = Path(path).read_text(encoding='utf-8')
    lines = text.splitlines()
    crons = re.findall(r"^\s*-\s*cron:\s*['\"]([^'\"]+)['\"]", text, re.M)
    on_block, jobs, current, in_jobs = [], {}, None, False
    for index, line in enumerate(lines):
        if re.match(r'^on:\s*$', line):
            for follow in lines[index + 1:]:
                if follow and not follow.startswith(' '):
                    break
                on_block.append(follow)
        if re.match(r'^jobs:\s*$', line):
            in_jobs = True
            continue
        if in_jobs:
            if line and not line.startswith(' '):
                in_jobs = False
                continue
            job = re.match(r'^  ([A-Za-z0-9_-]+):\s*$', line)
            if job:
                current = job.group(1)
                jobs[current] = {'timeout': None, 'concurrency': False}
            elif current and re.match(r'^    timeout-minutes:\s*(\d+)', line):
                jobs[current]['timeout'] = int(re.match(r'^    timeout-minutes:\s*(\d+)', line).group(1))
            elif current and re.match(r'^    concurrency:', line):
                jobs[current]['concurrency'] = True
    top_concurrency = bool(re.search(r'^concurrency:', text, re.M))
    return {'name': Path(path).name, 'crons': crons,
            'push': any(re.match(r'^  (push|pull_request):', l) for l in on_block),
            'concurrency': top_concurrency or bool(jobs) and all(j['concurrency'] for j in jobs.values()),
            'timeouts': {name: job['timeout'] for name, job in jobs.items()}}


def billed(minutes, jobs=1):
    return math.ceil(minutes) * jobs


def budget(root=ROOT, config=None, measurements=None):
    """Rows ``{workflow, runs, expected, worst}`` per month plus planned shows."""
    root = Path(root)
    measurements = measurements or json.loads((root / 'planning/workflow-minutes.json').read_text(encoding='utf-8'))
    if config is None:
        path = root / 'config.json'
        config = json.loads((path if path.is_file() else root / 'config.example.json').read_text(encoding='utf-8'))
    rows = []
    for path in sorted((root / '.github/workflows').glob('*.yml')):
        info = workflow_info(path)
        known = measurements['workflows'].get(info['name'])
        if not known:
            continue  # manual or experimental workflows are not part of the routine budget
        jobs = known.get('jobs', 1)
        worst_run = sum(t or 360 for t in info['timeouts'].values())  # GitHub default timeout: 360 min
        if known['kind'] == 'push':
            runs = known['runs_per_month']
            expected = runs * billed(known['minutes'], jobs)
        else:
            runs = sum(runs_per_month(c) for c in info['crons'])
            if known['kind'] == 'schedule_gated':
                due = min(runs, editions_per_month(config.get('automation', {})))
                expected = due * billed(known['due_minutes']) + (runs - due) * billed(known['idle_minutes'])
            else:
                media = min(runs, known.get('media_runs_per_month', 0))
                expected = (runs - media) * billed(known['minutes'], jobs) + media * billed(known.get('media_minutes', known['minutes']), jobs)
        rows.append({'workflow': info['name'], 'trigger': ', '.join(info['crons']) or 'push/PR',
                     'runs': runs, 'expected': expected, 'worst': runs * worst_run})
    shows = []
    try:
        try:
            from scripts.shows import resolve_shows
        except ModuleNotFoundError:
            from shows import resolve_shows
        resolved = resolve_shows(config) if 'shows' in config else []
    except ValueError:
        resolved = []
    for show in resolved:
        editions = editions_per_month(show['config'].get('automation', {}))
        shows.append({'show': show['id'], 'editions': editions,
                      'minutes_if_github': editions * billed(measurements['show_run_minutes'])})
    total = sum(r['expected'] for r in rows)
    return {'workflows': rows, 'shows': shows, 'total_expected': total,
            'total_worst': sum(r['worst'] for r in rows), 'quota_private': measurements['quota']['private_free_plan_minutes']}


def markdown(result):
    lines = ['| Workflow | Auslöser (UTC) | Läufe/Monat | erwartet (min) | Obergrenze Timeouts (min) |',
             '| --- | --- | ---: | ---: | ---: |']
    for row in result['workflows']:
        lines.append(f"| `{row['workflow']}` | `{row['trigger']}` | {row['runs']} | {row['expected']} | {row['worst']} |")
    lines.append(f"| **Summe** | | | **{result['total_expected']}** | {result['total_worst']} |")
    if result['shows']:
        lines += ['', '| Show | Ausgaben/Monat | Minuten, falls auf GitHub produziert |', '| --- | ---: | ---: |']
        lines += [f"| `{s['show']}` | {s['editions']} | {s['minutes_if_github']} |" for s in result['shows']]
    return '\n'.join(lines)


def crontab(config, root=ROOT, python='python3'):
    """One cron line per scheduled show; per-show lock plus a shared render lock."""
    try:
        from scripts.shows import resolve_shows
    except ModuleNotFoundError:
        from shows import resolve_shows
    root = Path(root)
    lines = ['# PersonalNewsHost shows – generated by scripts/show_schedule.py crontab',
             '# Per-show lock: a show never overlaps itself. Shared render lock: one production at a time.']
    for show in resolve_shows(config):
        automation = show['config'].get('automation', {})
        if not automation.get('enabled', False):
            lines.append(f"# {show['id']}: automation disabled")
            continue
        interval = automation.get('interval_hours', 1)
        if interval not in INTERVALS:
            raise ValueError('automation.interval_hours must be 1,2,3,4,6,8,12,24')
        start = automation.get('start_hour_local', 0)
        hours = ','.join(str(h) for h in sorted((start + i * interval) % 24 for i in range(24 // interval)))
        weekdays = {'daily': '*', 'weekdays': '1-5', 'weekends': '0,6'}[automation.get('days', 'daily')]
        locks = root / '.cache' / 'locks'
        command = (f"cd {shlex.quote(str(root))} && mkdir -p .cache/locks && "
                   f"flock -n {shlex.quote(str(locks / ('show-' + show['id'] + '.lock')))} "
                   f"flock -w 3000 {shlex.quote(str(locks / 'render.lock'))} "
                   f"{python} scripts/produce_show.py --show {shlex.quote(show['id'])} "
                   f">> .cache/show-{show['id']}.log 2>&1")
        lines += [f"CRON_TZ={automation.get('timezone', 'UTC')}", f"5 {hours} * * {weekdays} {command}"]
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['budget', 'crontab'])
    parser.add_argument('--config', type=Path)
    parser.add_argument('--private', action='store_true', help='Check against the 2000-minute quota of a private repository.')
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding='utf-8')) if args.config else None
    if args.action == 'crontab':
        print(crontab(config or json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))), end='')
        return 0
    result = budget(config=config)
    print(markdown(result))
    if args.private and result['total_expected'] > result['quota_private']:
        print(f"\nOver the private quota: {result['total_expected']} > {result['quota_private']} minutes", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
