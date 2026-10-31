"""Offline-first provider contracts, response validation and transactional cache.

No HTTP client, external adapter, tool execution or payment is implemented here.
"""
from contextlib import closing
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
import unicodedata
import uuid
from typing import Protocol

from jsonschema import Draft202012Validator

try:
    from .provider_budget import BudgetExceeded
    from .analysis_tasks import SCHEMAS, baseline
except ImportError:
    from provider_budget import BudgetExceeded
    from analysis_tasks import SCHEMAS, baseline

KINDS = {'text_generation', 'text_analysis', 'factcheck_source', 'video_generation', 'avatar_video', 'tts'}
FIELDS = {
    'text_generation': {'title', 'text', 'source_id', 'language'},
    'text_analysis': {'title', 'text', 'source_id', 'language'},
    'factcheck_source': {'claim', 'source_id', 'language'},
    'video_generation': {'prompt', 'duration_seconds', 'format'},
    'avatar_video': {'audio_ref', 'avatar_id', 'background_ref', 'format'},
    'tts': {'text', 'language', 'voice_id'},
}
TEXT_SCHEMA = {'type': 'object', 'required': ['text', 'source_ids'], 'additionalProperties': False,
               'properties': {'text': {'type': 'string', 'maxLength': 10000},
                              'source_ids': {'type': 'array', 'items': {'type': 'string'}}}}
ARTIFACT_SCHEMA = {'type': 'object', 'required': ['status', 'fixture_id'], 'additionalProperties': False,
                   'properties': {'status': {'const': 'mock'}, 'fixture_id': {'type': 'string'}}}
SECRET_PATTERN = re.compile(r'(?:\bsk-(?:ant-)?[A-Za-z0-9_-]{12,}|\bBearer\s+\S+|-----BEGIN .*PRIVATE KEY-----)')


class ProviderError(RuntimeError): pass
class ProviderTimeout(ProviderError): pass
class ProviderQuota(ProviderError): pass
class ProviderAuth(ProviderError): pass
class ProviderRejected(ProviderError): pass
class InvalidResponse(ProviderError): pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


@dataclass(frozen=True)
class Request:
    kind: str
    task: str
    model: str
    prompt_version: str
    payload: dict


class Provider(Protocol):
    id: str
    revision: str
    kind: str
    paid: bool
    def generate(self, request: Request, *, timeout_s: float) -> dict: ...


def filtered_request(request, secret_values=()):
    if request.kind not in KINDS:
        raise ValueError('Unsupported provider kind')
    for value in (request.task, request.model, request.prompt_version):
        if not isinstance(value, str) or not value or len(value) > 200:
            raise ValueError('Invalid request metadata')
    if not isinstance(request.payload, dict):
        raise ValueError('Provider payload must be an object')
    payload = {key: value for key, value in request.payload.items() if key in FIELDS[request.kind]}
    for key, value in payload.items():
        if key == 'duration_seconds':
            if type(value) not in (int, float) or not 0 < value <= 3600:
                raise ValueError('Invalid duration')
        elif not isinstance(value, str) or len(value) > 50000:
            raise ValueError('Payload fields must be bounded scalar data')
    serialized = canonical({'payload': payload, 'task': request.task, 'model': request.model, 'prompt_version': request.prompt_version})
    if SECRET_PATTERN.search(serialized) or any(secret and secret in serialized for secret in secret_values):
        raise ProviderRejected('Secret-like data in outgoing payload')
    # Payload remains data. No execution or interpretation of embedded instructions.
    return Request(request.kind, request.task, request.model, request.prompt_version, payload)


class Cache:
    """Serialize cache misses across processes; failed computations are rolled back."""
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS results (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        self.path.chmod(0o600)

    def get_or_compute(self, key, compute, validate):
        with closing(sqlite3.connect(self.path, timeout=30)) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT value FROM results WHERE key=?', (key,)).fetchone()
            if row:
                try:
                    value = json.loads(row[0])
                    validate(value)
                except (ValueError, InvalidResponse):
                    db.execute('DELETE FROM results WHERE key=?', (key,))
                else:
                    return value, True
            value = compute()
            validate(value)
            db.execute('INSERT OR REPLACE INTO results VALUES (?,?)', (key, canonical(value)))
            return value, False


class MockProvider:
    paid = False
    revision = 'extractive-fixtures-v1'
    def __init__(self, ident, kind):
        if kind not in KINDS:
            raise ValueError('Unsupported mock kind')
        self.id, self.kind, self.calls = ident, kind, 0

    def generate(self, request, *, timeout_s):
        self.calls += 1
        if self.kind == 'text_analysis' and request.task in SCHEMAS:
            return baseline(request.task, request.payload)
        if self.kind in {'text_generation', 'text_analysis'}:
            # Exact source excerpt, no claim of independent generation/verification.
            text = request.payload.get('text', request.payload.get('title', ''))[:1000]
            source_id = request.payload.get('source_id')
            return {'text': text, 'source_ids': [source_id] if source_id else []}
        return {'status': 'mock', 'fixture_id': hashlib.sha256(canonical(request.payload).encode()).hexdigest()}


class Runtime:
    def __init__(self, cache, *, secret_values=(), namespace='default', budget=None, run_id=None, audit_path=None):
        if not isinstance(namespace, str) or not namespace or len(namespace) > 200:
            raise ValueError('Invalid cache namespace')
        self.budget, self.run_id = budget, run_id or uuid.uuid4().hex
        self.audit_path = Path(audit_path) if audit_path else None
        self.namespace = namespace
        self.cache, self.secret_values = cache, tuple(secret_values)
        self.providers = {}

    def register(self, provider):
        if not isinstance(provider.id,str) or not provider.id or provider.id in self.providers or provider.kind not in KINDS:
            raise ValueError('Duplicate or invalid provider')
        if SECRET_PATTERN.search(provider.id) or any(secret and secret in provider.id for secret in self.secret_values):
            raise ValueError('Secret-like provider identifier')
        self.providers[provider.id] = provider

    def run(self, provider_id, request, *, schema=None, timeout_s=30, retries=0, fallback_to=None, before_attempt=None):
        if type(retries) is not int or not 0 <= retries <= 3 or not 0 < timeout_s <= 300:
            raise ValueError('Invalid timeout or retry count')
        request = filtered_request(request, self.secret_values)
        schema = schema or (SCHEMAS[request.task] if request.kind == 'text_analysis' and request.task in SCHEMAS else None) or (TEXT_SCHEMA if request.kind in {'text_generation', 'text_analysis'} else ARTIFACT_SCHEMA)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        def validate(value):
            try:
                canonical(value)
            except (TypeError, ValueError):
                raise InvalidResponse('Response is not finite JSON') from None
            if not validator.is_valid(value):
                raise InvalidResponse('Response does not match required schema')
            if SECRET_PATTERN.search(canonical(value)) or any(secret and secret in canonical(value) for secret in self.secret_values):
                raise InvalidResponse('Secret-like data in provider response')
        def execute(ident):
            provider = self.providers.get(ident)
            if provider is None or provider.kind != request.kind:
                raise ValueError('Unknown provider or incompatible kind')
            if provider.paid and (self.budget is None or not getattr(provider, 'billing_verified', False)):
                raise ProviderRejected('Paid execution requires verified cost ceiling and budget')
            key_data = {'namespace': self.namespace, 'provider': ident, 'revision': provider.revision, 'kind': request.kind,
                        'model': request.model, 'task': request.task, 'prompt_version': request.prompt_version,
                        'payload': request.payload, 'schema': schema}
            key = hashlib.sha256(canonical(key_data).encode()).hexdigest()
            def compute():
                for attempt in range(retries + 1):
                    try:
                        if before_attempt is not None:
                            before_attempt(ident)
                        if self.budget:
                            try:
                                self.budget.reserve(self.namespace, self.run_id, ident,
                                    getattr(provider, 'max_cost_eur', 0), getattr(provider, 'units', {}),
                                    rate_limit=getattr(provider, 'rate_limit', 0))
                            except BudgetExceeded:
                                raise ProviderQuota('Budget or quota reached') from None
                        if self.audit_path:
                            self.audit_path.parent.mkdir(parents=True, exist_ok=True)
                            with self.audit_path.open('a', encoding='utf-8') as log:
                                log.write(canonical({'provider':ident,'kind':request.kind,'task':request.task,
                                    'bytes':len(canonical(request.payload).encode()),'at':time.time()})+'\n')
                            self.audit_path.chmod(0o600)
                        result = provider.generate(request, timeout_s=timeout_s)
                        validate(result)
                        return result
                    except (ProviderTimeout, ProviderQuota, InvalidResponse):
                        if attempt == retries: raise
                        time.sleep(min(0.05 * 2**attempt, 1))
            value, cached = self.cache.get_or_compute(key, compute, validate)
            return {'value': value, 'provider_id': ident, 'cached': cached}
        try:
            return execute(provider_id)
        except ProviderError:
            if fallback_to is None or fallback_to == provider_id: raise
            return execute(fallback_to)
