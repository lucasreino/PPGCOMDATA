#!/usr/bin/env bash
# Daily backup for PPGCOMDATA (VPS).
#
# Backups include:
# - PostgreSQL database (pg_dump custom format)
# - Host folder ./data (Lattes XML + other persisted data)
# - Docker volume prod_uploads (uploads made by the API)
#
# Intended to be run on the VPS as the same user that owns the project
# (recommended: root via systemd timer).

set -euo pipefail
umask 077

PROJECT_DIR="${PPGCOMDATA_PROJECT_DIR:-/root/projects/ppgcomdata}"
COMPOSE_FILE="${PPGCOMDATA_COMPOSE_FILE:-docker-compose.prod.yml}"

BACKUP_ROOT="${BACKUP_ROOT:-/root/backups/ppgcomdata}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

PG_CONTAINER="${PG_CONTAINER_NAME:-ppgcomdata-db-prod}"
UPLOADS_VOLUME="${UPLOADS_VOLUME_NAME:-prod_uploads}"

timestamp="$(date +%F_%H-%M-%S)"
backup_dir="${BACKUP_ROOT}/${timestamp}"
mkdir -p "$backup_dir"

log() {
  echo "[backup] $*"
}

docker_env_value() {
  # Reads env vars from container config (best effort).
  # Example: docker_env_value ppgcomdata-db-prod POSTGRES_PASSWORD
  local container="$1"
  local key="$2"
  docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$container" \
    | awk -F= -v k="$key" '$1==k{print $2; exit}'
}

cleanup_old_backups() {
  # Avoid "find" to keep the script portable/safe.
  local now
  now="$(date +%s)"
  local retention_seconds=$((RETENTION_DAYS * 86400))

  shopt -s nullglob
  for d in "$BACKUP_ROOT"/*; do
    [[ -d "$d" ]] || continue
    # Only delete directories that match our timestamp format (YYYY-MM-DD_*)
    bn="$(basename "$d")"
    if [[ ! "$bn" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_ ]]; then
      continue
    fi
    mtime="$(stat -c %Y "$d" 2>/dev/null || echo 0)"
    if [[ "$mtime" == "0" ]]; then
      continue
    fi
    if (( now - mtime > retention_seconds )); then
      log "Removing old backup: $d"
      rm -rf "$d"
    fi
  done
}

log "Starting daily backup: $backup_dir"

db_running="$(docker inspect -f '{{.State.Running}}' "$PG_CONTAINER" 2>/dev/null || echo false)"
if [[ "$db_running" != "true" ]]; then
  log "ERROR: DB container '${PG_CONTAINER}' is not running."
  exit 1
fi

mkdir -p "$backup_dir"

log "Backing up PostgreSQL (pg_dump)..."
POSTGRES_USER="$(docker_env_value "$PG_CONTAINER" POSTGRES_USER || true)"
POSTGRES_PASSWORD="$(docker_env_value "$PG_CONTAINER" POSTGRES_PASSWORD || true)"
POSTGRES_DB="$(docker_env_value "$PG_CONTAINER" POSTGRES_DB || true)"

# Fallbacks (should match docker-compose defaults if env parsing fails).
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-change_me_in_production}"
POSTGRES_DB="${POSTGRES_DB:-ppgcomdata}"

export PGPASSWORD="$POSTGRES_PASSWORD"
docker exec \
  -e PGPASSWORD="$POSTGRES_PASSWORD" \
  "$PG_CONTAINER" \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom \
  > "$backup_dir/postgres.dump"
unset PGPASSWORD

log "Backing up uploads volume '${UPLOADS_VOLUME}'..."
docker run --rm \
  -v "${UPLOADS_VOLUME}:/data" \
  -v "${backup_dir}:/backup" \
  busybox:1.36 \
  sh -c 'tar czf /backup/uploads.tar.gz -C /data .'

log "Backing up host ./data folder..."
if [[ -d "${PROJECT_DIR}/data" ]]; then
  tar czf "$backup_dir/data.tar.gz" -C "$PROJECT_DIR" data
else
  log "WARNING: '${PROJECT_DIR}/data' not found; skipping data.tar.gz"
fi

log "Writing backup metadata..."
cat > "$backup_dir/metadata.txt" <<EOF
timestamp=$timestamp
project_dir=$PROJECT_DIR
backup_root=$BACKUP_ROOT
retention_days=$RETENTION_DAYS
pg_container=$PG_CONTAINER
uploads_volume=$UPLOADS_VOLUME
compose_file=$COMPOSE_FILE
EOF

log "Applying retention policy (keep last ${RETENTION_DAYS} days)..."
cleanup_old_backups

log "Backup completed successfully."

