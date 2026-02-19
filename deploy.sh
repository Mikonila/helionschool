#!/usr/bin/env bash
set -euo pipefail

VPS_HOST="77.73.232.142"
VPS_USER="root"
REMOTE_DIR="/root/helion_bot"
LOCAL_DIR="$(pwd)"

echo "==> Syncing project to VPS..."
rsync -av --delete --progress \
  --exclude venv \
  --exclude .venv \
  --exclude __pycache__ \
  --exclude "*.pyc" \
  --exclude ".git" \
  --exclude data \
  --exclude logs \
  "$LOCAL_DIR/" "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/"

echo "==> Deploying on VPS..."
ssh "${VPS_USER}@${VPS_HOST}" "REMOTE_DIR=${REMOTE_DIR} bash -s" <<'REMOTE'
set -euo pipefail
cd "${REMOTE_DIR}"
mkdir -p data logs

if docker compose version >/dev/null 2>&1; then
  docker compose down --remove-orphans || true
  docker rm -f helion_bot >/dev/null 2>&1 || true
  docker compose build --no-cache
  docker compose up -d --force-recreate
  docker compose ps
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose down --remove-orphans || true
  docker rm -f helion_bot >/dev/null 2>&1 || true
  docker-compose build --no-cache
  docker-compose up -d --force-recreate
  docker-compose ps
else
  echo 'ERROR: docker compose not found. Install docker-compose (hyphen) or Docker compose plugin.'
  exit 1
fi

docker logs --tail 120 helion_bot || true
REMOTE

echo "==> Done."
