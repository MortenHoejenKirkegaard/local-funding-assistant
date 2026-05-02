#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Update secrets before enabling external APIs."
fi

docker compose up -d
echo "Funding assistant services are starting."
echo "PostgreSQL: localhost:${POSTGRES_PORT:-5432}"
echo "Qdrant:     http://localhost:${QDRANT_PORT:-6333}"
