#!/usr/bin/env sh
set -eu

mkdir -p /app/data/issued /app/data/baked /app/data/backgrounds

# Seed runtime data only on first start. Existing files in /app/data are never
# overwritten, so upgrades do not destroy local templates or issued badges.
if [ -d /app/seed-data ]; then
  find /app/seed-data -maxdepth 1 -type f | while IFS= read -r source_file; do
    target_file="/app/data/$(basename "$source_file")"
    if [ ! -e "$target_file" ]; then
      cp "$source_file" "$target_file"
    fi
  done
fi

export BADGE83_HOST="${BADGE83_HOST:-0.0.0.0}"
export BADGE83_PORT="${BADGE83_PORT:-8000}"
export BADGE83_REGISTRY_DB="${BADGE83_REGISTRY_DB:-/app/data/registry.db}"

exec "$@"