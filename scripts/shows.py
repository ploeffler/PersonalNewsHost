"""Resolve isolated show configurations without changing the caller's configuration."""
from copy import deepcopy
import re

SHOW_ID = re.compile(r'^[a-z0-9][a-z0-9_-]{0,63}$')
SHOW_FIELDS = {'title', 'feeds', 'max_items', 'max_description_chars', 'language',
               'voice', 'presenter_settings', 'background', 'presenter', 'station_logo',
               'tts_engine', 'piper_length_scale', 'voice_pitch_semitones', 'editorial',
               'media', 'production', 'automation', 'target_duration_seconds',
               'feed_categories', 'category_filter', 'source_policy'}


def merge_objects(base, overrides):
    result = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_objects(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def resolve_shows(config):
    """Legacy config becomes main; explicit shows inherit fields, never other shows."""
    base = {key: deepcopy(value) for key, value in config.items() if key != 'shows'}
    if 'shows' not in config:
        return [{'id': 'main', 'title': base['title'], 'config': base}]
    shows = config['shows']
    if not isinstance(shows, list) or not shows:
        raise ValueError('shows must be a nonempty list')
    result, seen = [], set()
    for show in shows:
        if not isinstance(show, dict):
            raise ValueError('show must be an object')
        ident = show.get('id')
        if not isinstance(ident, str) or not SHOW_ID.fullmatch(ident) or ident in seen:
            raise ValueError('show IDs must be unique safe lowercase identifiers')
        if set(show) - SHOW_FIELDS - {'id', 'schedule', 'presenter', 'studio'}:
            raise ValueError('Unknown show configuration field')
        seen.add(ident)
        overrides = {key: value for key, value in show.items() if key in SHOW_FIELDS}
        # Existing renderer accepts portrait/background paths as presenter/studio.
        if 'studio' in show:
            overrides = merge_objects(overrides, {'presenter_settings': {'background': show['studio']}})
        if 'presenter' in show:
            overrides = merge_objects(overrides, {'presenter_settings': {'portrait': show['presenter']}})
        if 'schedule' in show:
            overrides['automation'] = merge_objects(base.get('automation', {}), show['schedule'])
        effective = merge_objects(base, overrides)
        result.append({'id': ident, 'title': effective['title'], 'config': effective})
    return result
