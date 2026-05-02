#!/usr/bin/env bash
set -euo pipefail

pkill -f "uvicorn funding_assistant.test_app:app" || true
echo "Test dashboard stopped if it was running."
