#!/usr/bin/env python3
"""Run a configured AI-provider request through the sole registry/runtime gateway."""
import argparse
import json
from pathlib import Path
import sys

try:
    from .configured_providers import configured_runtime
    from .provider_runtime import KINDS, ProviderError
except ImportError:
    from configured_providers import configured_runtime
    from provider_runtime import KINDS, ProviderError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config.json'))
    parser.add_argument('--kind', choices=sorted(KINDS), required=True)
    parser.add_argument('--input', type=Path, help='JSON payload file; stdin if omitted')
    parser.add_argument('--state', type=Path, default=Path('state/providers'))
    parser.add_argument('--provider')
    parser.add_argument('--task', default='generate')
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text())
        payload = json.loads(args.input.read_text() if args.input else sys.stdin.read())
        result = configured_runtime(config, args.state).run(args.kind, payload, task=args.task, provider_id=args.provider)
    except (OSError, ValueError, ProviderError):
        print('Provider request failed; check configuration and payload (values redacted).', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
