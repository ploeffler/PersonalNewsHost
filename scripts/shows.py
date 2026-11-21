"""Resolve isolated show configurations without changing the caller's configuration."""
from copy import deepcopy
import re

SHOW_ID = re.compile(r'^[a-z0-9][a-z0-9_-]{0,63}$')
SHOW_FIELDS = {'title', 'feeds', 'max_items', 'max_description_chars', 'language',
               'voice', 'presenter_settings', 'background', 'presenter', 'station_logo',
               'tts_engine', 'piper_length_scale', 'voice_pitch_semitones', 'editorial',
               'media', 'production', 'automation', 'target_duration_seconds',
               'feed_categories', 'category_filter', 'source_policy',
               'providers', 'provider_tasks', 'provider_budgets'}


def merge_objects(base, overrides):
    result = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_objects(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


HOST_FIELDS = {'name', 'gender', 'portrait', 'voice_model', 'voice', 'voice_pitch_semitones',
               'piper_length_scale', 'lip_sync'}
STUDIO_FIELDS = {'background', 'desk_foreground', 'scenes'}
VOICE_FIELDS = ('voice_model', 'voice', 'voice_pitch_semitones', 'piper_length_scale')


def _registry(config, key, fields):
    entries = config.get(key, {})
    if not isinstance(entries, dict):
        raise ValueError(f'{key} must be an object')
    for ident, entry in entries.items():
        if not SHOW_ID.fullmatch(str(ident)) or not isinstance(entry, dict):
            raise ValueError(f'{key} entries need safe lowercase IDs and objects')
        if set(entry) - fields:
            raise ValueError(f'Unknown {key} field')
    return entries


def voice_profile(host, base):
    """Voice settings for one host; missing values inherit from the show."""
    presenter = base.get('presenter_settings', {})
    profile = {'name': host.get('name', presenter.get('name', ''))}
    profile['voice_model'] = host.get('voice_model', presenter.get('voice_model'))
    for key in VOICE_FIELDS[1:]:
        if key in host:
            profile[key] = host[key]
        elif key in base:
            profile[key] = base[key]
    return {k: deepcopy(v) for k, v in profile.items() if v is not None}


def host_overrides(show, hosts, studios, base):
    """Translate host_id/studio_id/co_host_id into ordinary show fields."""
    overrides = {}
    for key, registry in (('host_id', hosts), ('co_host_id', hosts), ('studio_id', studios)):
        if key in show and show[key] not in registry:
            raise ValueError(f'Unknown {key}')
    if 'co_host_id' in show and 'host_id' not in show:
        raise ValueError('co_host_id requires host_id')
    if 'co_host_id' in show and show['co_host_id'] == show['host_id']:
        raise ValueError('co_host_id must differ from host_id')
    if 'studio_id' in show:
        overrides['presenter_settings'] = deepcopy(studios[show['studio_id']])
        overrides['studio_id'] = show['studio_id']
    if 'host_id' in show:
        host = hosts[show['host_id']]
        presenter = {k: deepcopy(v) for k, v in host.items() if k in {'name', 'gender', 'portrait', 'voice_model', 'lip_sync'}}
        overrides = merge_objects(overrides, {'presenter_settings': presenter})
        overrides.update({k: deepcopy(host[k]) for k in VOICE_FIELDS[1:] if k in host})
        overrides['host_id'] = show['host_id']
        # Alternating moderation: stories alternate between the voices (visual stays the main host).
        effective = merge_objects(base, overrides)
        profiles = [voice_profile(host, effective)]
        if 'co_host_id' in show:
            profiles.append(voice_profile(hosts[show['co_host_id']], effective))
            overrides['co_host_id'] = show['co_host_id']
        overrides['voice_profiles'] = profiles
    return overrides


def resolve_shows(config):
    """Legacy config becomes main; explicit shows inherit fields, never other shows."""
    base = {key: deepcopy(value) for key, value in config.items() if key not in ('shows', 'hosts', 'studios')}
    if 'shows' not in config:
        base = {key: deepcopy(value) for key, value in config.items() if key != 'shows'}
        return [{'id': 'main', 'title': base['title'], 'config': base}]
    shows = config['shows']
    if not isinstance(shows, list) or not shows:
        raise ValueError('shows must be a nonempty list')
    hosts = _registry(config, 'hosts', HOST_FIELDS)
    studios = _registry(config, 'studios', STUDIO_FIELDS)
    result, seen = [], set()
    for show in shows:
        if not isinstance(show, dict):
            raise ValueError('show must be an object')
        ident = show.get('id')
        if not isinstance(ident, str) or not SHOW_ID.fullmatch(ident) or ident in seen:
            raise ValueError('show IDs must be unique safe lowercase identifiers')
        if set(show) - SHOW_FIELDS - {'id', 'schedule', 'presenter', 'studio', 'host_id', 'studio_id', 'co_host_id'}:
            raise ValueError('Unknown show configuration field')
        seen.add(ident)
        # Registry entries first; explicit fields of the show still win.
        overrides = merge_objects(host_overrides(show, hosts, studios, base),
                                  {key: value for key, value in show.items() if key in SHOW_FIELDS})
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
