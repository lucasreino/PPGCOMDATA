#!/usr/bin/env bash
# Aplica perfis Scholar na VPS (migração + cruzamento com produções).
# Uso: ssh hermes-vps 'bash -s' < scripts/vps-scholar-profiles.sh
set -euo pipefail

PROJECT_DIR="${PPGCOMDATA_PROJECT_DIR:-/root/projects/ppgcomdata}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "$PROJECT_DIR"
git fetch origin main
git reset --hard origin/main

docker compose -f "$COMPOSE_FILE" exec -T api alembic upgrade head
docker compose -f "$COMPOSE_FILE" exec -T api python -m app.apply_scholar_profiles
docker compose -f "$COMPOSE_FILE" exec -T api python -m app.verify_scholar_apply

echo "==> Rebuild web (exibir citações na UI)..."
docker compose -f "$COMPOSE_FILE" build web
docker compose -f "$COMPOSE_FILE" up -d web api
