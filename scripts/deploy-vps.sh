#!/usr/bin/env bash
# Deploy PPGCOMDATA on the VPS (production).
# Run on the server: bash scripts/deploy-vps.sh
# Or from your machine: ssh hermes-vps 'bash -s' < scripts/deploy-vps.sh
set -euo pipefail

PROJECT_DIR="${PPGCOMDATA_PROJECT_DIR:-/root/projects/ppgcomdata}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BRANCH="${DEPLOY_BRANCH:-main}"
NO_CACHE="${NO_CACHE:-0}"
NO_CACHE_WEB="${NO_CACHE_WEB:-0}"
HEALTH_TIMEOUT="${DEPLOY_HEALTH_TIMEOUT_SEC:-300}"
HEALTH_INTERVAL="${DEPLOY_HEALTH_INTERVAL_SEC:-5}"
API_HEALTH_URL="${API_HEALTH_URL:-http://127.0.0.1:8000/}"

cd "$PROJECT_DIR"

echo "==> Syncing git (${BRANCH})..."
git fetch origin "$BRANCH"
git reset --hard "origin/${BRANCH}"

echo "==> Building web and api..."
if [[ "$NO_CACHE_WEB" == "1" || "$NO_CACHE_WEB" == "true" ]]; then
  docker compose -f "$COMPOSE_FILE" build --no-cache web
  docker compose -f "$COMPOSE_FILE" build api
elif [[ "$NO_CACHE" == "1" || "$NO_CACHE" == "true" ]]; then
  docker compose -f "$COMPOSE_FILE" build --no-cache web api
else
  docker compose -f "$COMPOSE_FILE" build web api
fi

echo "==> Starting services..."
docker compose -f "$COMPOSE_FILE" up -d web api

echo "==> Container status:"
docker compose -f "$COMPOSE_FILE" ps

echo "==> Waiting for API and web (timeout ${HEALTH_TIMEOUT}s)..."
elapsed=0
while (( elapsed < HEALTH_TIMEOUT )); do
  api_ok=0
  web_ok=0

  if curl -sf "$API_HEALTH_URL" >/dev/null 2>&1; then
    api_ok=1
  fi

  web_state="$(docker compose -f "$COMPOSE_FILE" ps web --format '{{.State}}' 2>/dev/null | head -n1 || true)"
  if [[ "$web_state" == "running" ]]; then
    web_ok=1
  fi

  if (( api_ok == 1 && web_ok == 1 )); then
    echo "==> Health check passed."
    docker compose -f "$COMPOSE_FILE" ps
    exit 0
  fi

  sleep "$HEALTH_INTERVAL"
  elapsed=$((elapsed + HEALTH_INTERVAL))
done

echo "ERROR: Health check timed out after ${HEALTH_TIMEOUT}s." >&2
docker compose -f "$COMPOSE_FILE" ps
docker compose -f "$COMPOSE_FILE" logs --tail=80 api web
exit 1
