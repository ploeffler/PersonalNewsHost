#!/usr/bin/env python3
"""Shared Linux/container entry point; production and public preview stay separate."""
import argparse
import datetime as dt
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def layout(root=ROOT):
    root = Path(root).resolve()
    return {name: root / relative for name, relative in {
        'config': 'config.json', 'models': 'models', 'assets': 'assets',
        'state': 'state', 'provider_state': 'state/providers',
        'productions': 'out/productions', 'public': 'out/public',
        'archive': 'archive',
    }.items()}


def configured_show(path, ident):
    try:
        from .validate_config import validate_config
        from .shows import resolve_shows
    except ImportError:
        from validate_config import validate_config
        from shows import resolve_shows
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    validate_config(config)
    show = next((item for item in resolve_shows(config) if item['id'] == ident), None)
    if show is None:
        raise ValueError('Unknown show ID')
    return config, show


def due(config_path, ident, paths, now=None):
    try:
        from .check_schedule import production_due, published_at
    except ImportError:
        from check_schedule import production_due, published_at
    _, show = configured_show(config_path, ident)
    settings = show['config'].get('automation', {})
    now = now or dt.datetime.now(dt.timezone.utc)
    published = published_at(paths['productions'] / show['id'] / 'feed.xml')
    enabled, slot, reason = production_due(settings, now, published, manual=False)
    return {'show': show['id'], 'due': enabled, 'slot_utc': slot.isoformat() if slot else None,
            'timezone': settings.get('timezone', 'UTC'), 'reason': reason}


def produce(config_path, ident, paths):
    config, _ = configured_show(config_path, ident)
    try:
        from .produce_show import produce as produce_show
    except ImportError:
        from produce_show import produce as produce_show
    return produce_show(config, ident, paths['productions'])


def preview(paths, port):
    if not 1024 <= port <= 65535:
        raise ValueError('Preview port must be 1024..65535')
    public = paths['public']
    if not public.is_dir():
        raise ValueError('Public preview directory does not exist')
    # Stdlib's static handler follows symlinks. Refuse them in the preview tree
    # so private state cannot be served through a prepared symlink.
    if public.is_symlink() or any(path.is_symlink() for path in public.rglob('*')):
        raise ValueError('Public preview must not contain symlinks')
    handler = partial(SimpleHTTPRequestHandler, directory=str(public))
    with ThreadingHTTPServer(('127.0.0.1', port), handler) as server:
        server.serve_forever()


def main(argv=None):
    paths = layout()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['inspect', 'due', 'produce', 'serve-preview', 'check-updates', 'watch-updates'])
    parser.add_argument('--config', type=Path, default=paths['config'])
    parser.add_argument('--show', default='main')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args(argv)
    try:
        if args.command in ('check-updates', 'watch-updates'):
            try:
                from .update_check import main as update_main
            except ImportError:
                from update_check import main as update_main
            return update_main(['--watch'] if args.command == 'watch-updates' else [])
        if args.command == 'inspect':
            print(json.dumps({'paths': {key: str(value) for key, value in paths.items()},
                              'config': str(args.config.resolve()),
                              'preview_bind': '127.0.0.1', 'preview_port': args.port,
                              'publishes_automatically': False}, indent=2))
        elif args.command == 'due':
            print(json.dumps(due(args.config, args.show, paths)))
        elif args.command == 'produce':
            print(produce(args.config, args.show, paths))
        else:
            preview(paths, args.port)
    except (OSError, ValueError):
        print('Runtime operation failed; check paths, permissions and configuration (values redacted).', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
