#!/usr/bin/env bash
# PersonalNewsHost: status (siehe docs/guide/dienst.md)
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
PYTHON=".venv-pnh/bin/python"
[ -x "$PYTHON" ] || PYTHON="$(command -v python3)"
exec "$PYTHON" scripts/service.py status "$@"
