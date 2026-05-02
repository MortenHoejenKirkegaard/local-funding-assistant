#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -d "$ROOT_DIR/.venv" ]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.venv/bin/activate"
fi

if ! python3 -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo "FastAPI dependencies are not installed yet."
  echo "Run: python3 -m venv .venv"
  echo "Then: .venv/bin/python -m pip install -e '.[test]'"
  exit 1
fi

PYTHONPATH="$ROOT_DIR/src" python3 -m uvicorn funding_assistant.test_app:app --host 127.0.0.1 --port 3000
