"""Configured AI-provider gateway. Version 0.1 admits local mock adapters only.

RSS/media downloads and publication transports are not AI providers. No external
AI SDK or endpoint is executed here; future adapters must implement Provider and
be admitted explicitly. Budget/accounting and analysis tasks have separate tasks.
"""
from collections import deque
import re
import threading
import time
from pathlib import Path

try:
    from .provider_runtime import Cache, KINDS, MockProvider, ProviderError, ProviderQuota, Request, Runtime
except ImportError:
    from provider_runtime import Cache, KINDS, MockProvider, ProviderError, ProviderQuota, Request, Runtime

IDENT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$')


def validate_provider_specs(specs):
    """Validate cross-reference semantics in addition to the JSON schema."""
    if not isinstance(specs, list):
        raise ValueError('Providers must be a list')
    by_id = {}
    for spec in specs:
        if not isinstance(spec, dict) or not IDENT.fullmatch(str(spec.get('id', ''))) or spec.get('kind') not in KINDS:
            raise ValueError('Invalid provider identity or kind')
        if spec['id'] in by_id:
            raise ValueError('Duplicate provider IDs')
        if spec.get('adapter', 'mock') != 'mock':
            raise ValueError('Only mock adapters are executable in version 0.1')
        if spec.get('endpoint', '') or spec.get('cost_model', {}).get('max_cost_eur', 0) != 0:
            raise ValueError('Mock providers require no endpoint and zero cost')
        by_id[spec['id']] = spec
    for spec in specs:
        seen = {spec['id']}
        fallback = spec.get('fallback_to')
        while fallback:
            target = by_id.get(fallback)
            if target is None or fallback in seen or target['kind'] != spec['kind']:
                raise ValueError('Invalid provider fallback chain')
            if spec.get('enabled', False) and not target.get('enabled', False):
                raise ValueError('Enabled provider requires enabled fallback')
            seen.add(fallback)
            fallback = target.get('fallback_to')
    return by_id


class ProviderRegistry:
    """Select enabled providers by priority, route every invocation via Runtime.

    rate_limit is calls per minute in this process (0 = unlimited). It is an
    execution throttle, not durable quota/billing. Every actual adapter attempt
    counts, including retries; cache hits do not. Secrets are never resolved.
    """
    def __init__(self, config, state, *, namespace='default', clock=time.monotonic):
        try:
            from .validate_config import validate_config
        except ImportError:
            from validate_config import validate_config
        validate_config(config)
        self.specs = validate_provider_specs(config.get('providers', []))
        self.runtime = Runtime(Cache(Path(state) / 'provider-cache.sqlite'), namespace=namespace)
        self.clock = clock
        self.calls = {}
        self.lock = threading.Lock()
        for spec in self.specs.values():
            if spec.get('enabled', False):
                self.runtime.register(MockProvider(spec['id'], spec['kind']))

    def run(self, kind, payload, *, task='generate', prompt_version='v1', provider_id=None, schema=None):
        if kind not in KINDS:
            raise ValueError('Unknown provider kind')
        candidates = sorted((s for s in self.specs.values() if s['kind'] == kind and s.get('enabled', False)),
                            key=lambda s: (s.get('priority', 100), s['id']))
        if provider_id is None:
            if not candidates:
                raise ValueError('No enabled provider for requested kind')
            provider_id = candidates[0]['id']
        visited = set()
        while provider_id:
            spec = self.specs.get(provider_id)
            if spec is None or not spec.get('enabled', False) or spec['kind'] != kind or provider_id in visited:
                raise ValueError('Unknown, disabled or incompatible provider')
            visited.add(provider_id)
            try:
                def before_attempt(ident):
                    with self.lock:
                        now = self.clock()
                        calls = self.calls.setdefault(ident, deque())
                        while calls and now - calls[0] >= 60:
                            calls.popleft()
                        limit = self.specs[ident].get('rate_limit', 0)
                        if limit and len(calls) >= limit:
                            raise ProviderQuota('Provider rate limit reached')
                        calls.append(now)
                request = Request(kind, task, spec.get('model', 'mock-v1'), prompt_version, payload)
                return self.runtime.run(provider_id, request, schema=schema,
                                        timeout_s=spec.get('timeout_s', 30), retries=spec.get('retries', 0),
                                        before_attempt=before_attempt)
            except ProviderError:
                fallback = spec.get('fallback_to')
                if not fallback:
                    raise
                provider_id = fallback


def configured_runtime(config, state, namespace='default'):
    return ProviderRegistry(config, state, namespace=namespace)
