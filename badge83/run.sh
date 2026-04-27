#!/usr/bin/env bash
# Wrapper de compatibilité : le lancement sécurisé passe par badge83.sh,
# qui charge badge83.env et démarre Uvicorn sur BADGE83_HOST:BADGE83_PORT.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/badge83.sh" start