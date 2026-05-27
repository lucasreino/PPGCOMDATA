#!/usr/bin/env bash
# Daily backup for PPGCOMDATA (VPS).
#
# Backups include:
# - PostgreSQL database (pg_dump custom format)
# - Host folder ./data (Lattes XML + other persisted data)
# - Docker volume prod_uploads (uploads made by the API)
#
# Optional: upload to Google Drive (or any rclone remote) when RCLONE_REMOTE is set.
# See docs/BACKUP.md for setup.
#
# Intended to be run on the VPS as the same user that owns the project
# (recommended: root via systemd timer).

set -euo pipefail
umask 077

PROJECT_DIR="${PPGCOMDATA_PROJECT_DIR:-/root/projects/ppgcomdata}"
COMPOSE_FILE="${PPGCOMDATA_COMPOSE_FILE:-docker-compose.prod.yml}"

BACKUP_ROOT="${BACKUP_ROOT:-/root/backups/ppgcomdata}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
GDRIVE_RETENTION_DAYS="${GDRIVE_RETENTION_DAYS:-30}"

PG_CONTAINER="${PG_CONTAINER_NAME:-ppgcomdata-db-prod}"
UPLOADS_VOLUME="${UPLOADS_VOLUME_NAME:-prod_uploads}"

RCLONE_REMOTE="${RCLONE_REMOTE:-}"
RCLONE_CONFIG="${RCLONE_CONFIG:-/root/.config/rclone/rclone.conf}"

timestamp="$(date +%F_%H-%M-%S)"
backup_dir="${BACKUP_ROOT}/${timestamp}"
mkdir -p "$backup_dir"

log() {
  echo "[backup] $*"
}

docker_env_value() {
  local container="$1"
  local key="$2"
  docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$container" \
    | awk -F= -v k="$key" '$1==k{print $2; exit}'
}

is_backup_dir_name() {
  [[ "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}$ ]]
}

cleanup_old_backups() {
  local now
  now="$(date +%s)"
  local retention_seconds=$((RETENTION_DAYS * 86400))

  shopt -s nullglob
  for d in "$BACKUP_ROOT"/*; do
    [[ -d "$d" ]] || continue
    bn="$(basename "$d")"
    if ! is_backup_dir_name "$bn"; then
      continue
    fi
    mtime="$(stat -c %Y "$d" 2>/dev/null || echo 0)"
    if [[ "$mtime" == "0" ]]; then
      continue
    fi
    if (( now - mtime > retention_seconds )); then
      log "Removing old local backup: $d"
      rm -rf "$d"
    fi
  done
}

cleanup_old_remote_backups() {
  local remote="${RCLONE_REMOTE%/}"
  local retention="${GDRIVE_RETENTION_DAYS:-0}"
  if [[ "$retention" -le 0 ]]; then
    return 0
  fi

  local now retention_seconds
  now="$(date +%s)"
  retention_seconds=$((retention * 86400))

  log "Applying remote retention (keep last ${retention} days) on ${remote}..."
  while IFS= read -r name; do
    [[ -n "$name" ]] || continue
    name="${name%/}"
    if ! is_backup_dir_name "$name"; then
      continue
    fi

    # Parse YYYY-MM-DD from folder name.
    local y m d
    IFS='-' read -r y m d <<< "${name%%_*}"
    local hms="${name#*_}"
    local hh mm ss
    IFS='-' read -r hh mm ss <<< "$hms"
    local backup_ts
    backup_ts="$(date -d "${y}-${m}-${d} ${hh}:${mm}:${ss}" +%s 2>/dev/null || echo 0)"
    if [[ "$backup_ts" == "0" ]]; then
      continue
    fi
    if (( now - backup_ts > retention_seconds )); then
      log "Removing old remote backup: ${remote}/${name}"
      rclone purge "${remote}/${name}"
    fi
  done < <(rclone lsf "$remote" --dirs-only --config "$RCLONE_CONFIG" 2>/dev/null || true)
}

upload_backup() {
  local remote="${RCLONE_REMOTE:-}"
  if [[ -z "$remote" ]]; then
    return 0
  fi

  if ! command -v rclone >/dev/null 2>&1; then
    log "ERROR: rclone is not installed but RCLONE_REMOTE is set."
    log "Install with: curl https://rclone.org/install.sh | sudo bash"
    exit 1
  fi

  if [[ ! -f "$RCLONE_CONFIG" ]]; then
    log "ERROR: rclone config not found at ${RCLONE_CONFIG}"
    exit 1
  fi

  local remote_path="${remote%/}/${timestamp}"
  log "Uploading backup to ${remote_path}..."
  if ! rclone copy "$backup_dir" "$remote_path" \
    --config "$RCLONE_CONFIG" \
    --transfers 2 \
    --checkers 4 \
    --contimeout 60s \
    --timeout 300s \
    --low-level-retries 3; then
    log "WARNING: Remote upload failed. Local backup was kept."
    log "For personal Gmail Drive, use OAuth (not service account). See docs/BACKUP.md"
    return 0
  fi

  log "Remote upload completed."
  cleanup_old_remote_backups
}

log "Starting daily backup: $backup_dir"

db_running="$(docker inspect -f '{{.State.Running}}' "$PG_CONTAINER" 2>/dev/null || echo false)"
if [[ "$db_running" != "true" ]]; then
  log "ERROR: DB container '${PG_CONTAINER}' is not running."
  exit 1
fi

log "Backing up PostgreSQL (pg_dump)..."
POSTGRES_USER="$(docker_env_value "$PG_CONTAINER" POSTGRES_USER || true)"
POSTGRES_PASSWORD="$(docker_env_value "$PG_CONTAINER" POSTGRES_PASSWORD || true)"
POSTGRES_DB="$(docker_env_value "$PG_CONTAINER" POSTGRES_DB || true)"

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
gdrive_retention_days=$GDRIVE_RETENTION_DAYS
rclone_remote=$RCLONE_REMOTE
pg_container=$PG_CONTAINER
uploads_volume=$UPLOADS_VOLUME
compose_file=$COMPOSE_FILE
EOF

upload_backup

log "Applying local retention policy (keep last ${RETENTION_DAYS} days)..."
cleanup_old_backups

log "Backup completed successfully."
