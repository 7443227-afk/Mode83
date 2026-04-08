#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$ROOT_DIR/badge83"
VENV_DIR="$APP_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

if [ ! -d "$APP_DIR" ]; then
  echo "Erreur: dossier badge83 introuvable dans $ROOT_DIR" >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "[badge.sh] Création de l'environnement virtuel..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "[badge.sh] Installation / vérification des dépendances..."
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "[badge.sh] Démarrage de Badge83 sur http://$HOST:$PORT"
cd "$APP_DIR"
exec "$VENV_DIR/bin/uvicorn" app.main:app --host "$HOST" --port "$PORT" --reload