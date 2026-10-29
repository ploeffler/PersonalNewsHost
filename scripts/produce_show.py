#!/usr/bin/env python3
"""Produce a selected show into out/<show_id>; never invoke external publishers."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import threading

try:
    from . import generate
    from .shows import resolve_shows
    from .validate_config import validate_config
except ImportError:
    import generate
    from shows import resolve_shows
    from validate_config import validate_config

_RENDER_LOCK = threading.RLock()


@contextmanager
def show_context(config, destination, base_url):
    # Legacy renderer uses globals. Serialize access and restore even after errors.
    with _RENDER_LOCK:
        old = generate.CONFIG, generate.DOCS, generate.BASE, deepcopy(generate.FEED_DATES)
        generate.CONFIG, generate.DOCS, generate.BASE = deepcopy(config), destination, base_url
        generate.FEED_DATES.clear()
        try:
            yield
        finally:
            generate.CONFIG, generate.DOCS, generate.BASE = old[:3]
            generate.FEED_DATES.clear()
            generate.FEED_DATES.update(old[3])


def produce(config, show_id, output_root, base_url=None):
    validate_config(config)
    shows = resolve_shows(config)
    show = next((item for item in shows if item['id'] == show_id), None)
    if show is None:
        raise ValueError('Unknown show ID')
    root = Path(output_root).resolve()
    destination = (root / show_id).resolve()
    if destination.parent != root:
        raise ValueError('Show output must remain inside output root')
    destination.mkdir(parents=True, exist_ok=True)
    # Local production links stay relative unless deployment explicitly supplies a URL.
    url = base_url.rstrip('/') + '/' if base_url else './'
    with show_context(show['config'], destination, url):
        generate.main()
    (destination / 'show.json').write_text(json.dumps({
        'show_id': show_id, 'title': show['title'], 'status': 'produced',
        'publication_requested': False,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=generate.ROOT / 'config.json')
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--show')
    choice.add_argument('--list', action='store_true')
    parser.add_argument('--output-root', type=Path, default=generate.ROOT / 'out')
    parser.add_argument('--base-url', help='Explicit URL for this show, otherwise relative links')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    validate_config(config)
    if args.list:
        for show in resolve_shows(config):
            print(f"{show['id']}: {show['title']}")
    else:
        print(produce(config, args.show, args.output_root, args.base_url))


if __name__ == '__main__':
    main()
