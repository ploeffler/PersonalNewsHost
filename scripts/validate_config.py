#!/usr/bin/env python3
"""Validate configuration locally; errors never echo configuration values/secrets."""
import argparse
import json
import math
from pathlib import Path
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def validate_config(config):
    schema = json.loads((ROOT / 'config.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(config),
                    key=lambda error: str(list(error.absolute_path)))
    if errors:
        # Validator messages include actual values; only expose path and rule.
        error = errors[0]
        path = '.'.join(map(str, error.absolute_path)) or '<root>'
        raise ValueError(f'Invalid configuration at {path}: rule {error.validator}')
    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('Configuration contains a non-finite number')
        if isinstance(value, dict):
            for item in value.values(): finite(item)
        elif isinstance(value, list):
            for item in value: finite(item)
    finite(config)
    if 'shows' in config:
        try:
            from .shows import resolve_shows
        except ImportError:
            from shows import resolve_shows
        for show in resolve_shows(config):
            validate_config(show['config'])
    timezone = config.get('automation', {}).get('timezone', 'UTC')
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError('Invalid configuration at automation.timezone') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', default=['config.json', 'config.example.json'])
    args = parser.parse_args()
    for name in args.paths:
        try:
            config = json.loads(Path(name).read_text(encoding='utf-8'))
            validate_config(config)
        except (OSError, ValueError) as exc:
            if isinstance(exc, json.JSONDecodeError):
                message = f'Invalid JSON at line {exc.lineno}, column {exc.colno}'
            elif isinstance(exc, OSError):
                message = 'Cannot read configuration file'
            else:
                message = str(exc)
            print(f'{Path(name).name}: {message}', file=sys.stderr)
            return 1
        print(f'{Path(name).name}: valid')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
