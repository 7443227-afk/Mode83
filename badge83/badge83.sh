#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/home/ubuntu/projects/Mode83/badge83"
WORKSPACE_DIR="/home/ubuntu/projects/Mode83"
ROOT_VENV_PYTHON="$WORKSPACE_DIR/.venv/bin/python"
PROJECT_VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
if [ -x "$ROOT_VENV_PYTHON" ]; then
  VENV_PYTHON="$ROOT_VENV_PYTHON"
else
  VENV_PYTHON="$PROJECT_VENV_PYTHON"
fi
APP_MODULE="app.main:app"
PID_FILE="$PROJECT_DIR/server.pid"
LOG_FILE="$PROJECT_DIR/server.log"
CONFIG_FILE="$PROJECT_DIR/badge83.env"

DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"
DEFAULT_PUBLIC_SCHEME="http"
DEFAULT_PUBLIC_HOST="mode83.ddns.net"
DEFAULT_SEARCH_PEPPER="badge83-dev-search-pepper"

if [ -f "$CONFIG_FILE" ]; then
  # shellcheck disable=SC1090
  set -a
  source "$CONFIG_FILE"
  set +a
fi

HOST="${BADGE83_HOST:-$DEFAULT_HOST}"
PORT="${BADGE83_PORT:-$DEFAULT_PORT}"
PUBLIC_SCHEME="${BADGE83_PUBLIC_SCHEME:-$DEFAULT_PUBLIC_SCHEME}"
PUBLIC_HOST="${BADGE83_PUBLIC_HOST:-$DEFAULT_PUBLIC_HOST}"
PUBLIC_PORT="${BADGE83_PUBLIC_PORT:-$PORT}"
if [ -n "${BADGE83_BASE_URL:-}" ]; then
  BASE_URL="${BADGE83_BASE_URL%/}"
elif { [ "$PUBLIC_SCHEME" = "http" ] && [ "$PUBLIC_PORT" = "80" ]; } || { [ "$PUBLIC_SCHEME" = "https" ] && [ "$PUBLIC_PORT" = "443" ]; }; then
  BASE_URL="$PUBLIC_SCHEME://$PUBLIC_HOST"
else
  BASE_URL="$PUBLIC_SCHEME://$PUBLIC_HOST:$PUBLIC_PORT"
fi
SEARCH_PEPPER="${BADGE83_SEARCH_PEPPER:-$DEFAULT_SEARCH_PEPPER}"

usage() {
  cat <<USAGE
Gestionnaire du serveur Badge83

Utilisation :
  ./badge83.sh start
  ./badge83.sh stop
  ./badge83.sh restart
  ./badge83.sh status
  ./badge83.sh logs

Fichier de configuration :
  $CONFIG_FILE

Variables d'environnement optionnelles :
  BADGE83_HOST      Hôte d'écoute (défaut : $DEFAULT_HOST)
  BADGE83_PORT      Port d'écoute (défaut : $DEFAULT_PORT)
  BADGE83_BASE_URL  URL publique explicite intégrée dans les badges
  BADGE83_PUBLIC_SCHEME  Schéma public si BADGE83_BASE_URL n'est pas défini (défaut : $DEFAULT_PUBLIC_SCHEME)
  BADGE83_PUBLIC_HOST    Nom d'hôte public si BADGE83_BASE_URL n'est pas défini (défaut : $DEFAULT_PUBLIC_HOST)
  BADGE83_PUBLIC_PORT    Port public si BADGE83_BASE_URL n'est pas défini (défaut : BADGE83_PORT)
  BADGE83_SEARCH_PEPPER  Pepper stable pour les hash de recherche admin

Exemples :
  ./badge83.sh start
  BADGE83_PUBLIC_HOST=mode83.ddns.net ./badge83.sh restart
  BADGE83_PORT=8010 BADGE83_PUBLIC_PORT=8010 ./badge83.sh start
  BADGE83_PUBLIC_SCHEME=https BADGE83_PUBLIC_PORT=443 ./badge83.sh start
USAGE
}

ensure_project() {
  cd "$PROJECT_DIR"
  if [ ! -x "$VENV_PYTHON" ]; then
    echo "Erreur : Python du virtualenv introuvable à l'emplacement $VENV_PYTHON"
    echo "Créez-le avec : python3 -m venv /home/ubuntu/projects/Mode83/.venv"
    echo "Installez ensuite les dépendances avec : /home/ubuntu/projects/Mode83/.venv/bin/pip install -r /home/ubuntu/projects/Mode83/badge83/requirements.txt"
    exit 1
  fi
}

running_pid() {
  if [ -f "$PID_FILE" ]; then
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo "$pid"
      return 0
    fi
  fi

  local pid_by_port
  pid_by_port="$(ss -ltnp 2>/dev/null | awk -v port=":$PORT" '$4 ~ port { if (match($0, /pid=[0-9]+/)) { print substr($0, RSTART + 4, RLENGTH - 4); exit } }')"
  if [ -n "$pid_by_port" ]; then
    echo "$pid_by_port"
    return 0
  fi

  local pids
  pids="$(pgrep -f "uvicorn $APP_MODULE --host .* --port $PORT" || true)"
  if [ -n "$pids" ]; then
    echo "$pids" | head -n 1
    return 0
  fi

  return 1
}

show_status() {
  ensure_project
  local pid
  if pid="$(running_pid)"; then
    echo "Statut     : ACTIF"
    echo "PID        : $pid"
    echo "Écoute     : $HOST:$PORT"
    echo "URL de base: $BASE_URL"
    echo "Fichier PID: $PID_FILE"
    echo "Fichier log: $LOG_FILE"
    ss -ltnp 2>/dev/null | grep ":$PORT" || true
  else
    echo "Statut     : ARRÊTÉ"
    echo "Écoute     : $HOST:$PORT"
    echo "URL de base: $BASE_URL"
    echo "Fichier PID: $PID_FILE"
    echo "Fichier log: $LOG_FILE"
  fi
}

start_server() {
  ensure_project
  local pid
  if pid="$(running_pid)"; then
    echo "Badge83 est déjà en cours d'exécution (PID $pid)."
    show_status
    return 0
  fi

  echo "Démarrage de Badge83..."
  echo "- Hôte     : $HOST"
  echo "- Port     : $PORT"
  echo "- URL base : $BASE_URL"

  export BADGE83_BASE_URL="$BASE_URL"
  export BADGE83_SEARCH_PEPPER="$SEARCH_PEPPER"
  nohup "$VENV_PYTHON" -m uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 < /dev/null &
  local new_pid=$!
  echo "$new_pid" > "$PID_FILE"
  sleep 2

  local effective_pid
  effective_pid="$(running_pid || true)"
  if [ -n "$effective_pid" ] && kill -0 "$effective_pid" 2>/dev/null; then
    echo "$effective_pid" > "$PID_FILE"
    echo "Démarré. PID : $effective_pid"
    show_status
  else
    echo "Échec du démarrage de Badge83. Dernières lignes du log :"
    tail -n 20 "$LOG_FILE" || true
    exit 1
  fi
}

stop_server() {
  ensure_project
  local pid
  if ! pid="$(running_pid)"; then
    echo "Badge83 n'est pas en cours d'exécution."
    rm -f "$PID_FILE"
    return 0
  fi

  echo "Arrêt de Badge83 (PID $pid)..."
  kill "$pid" 2>/dev/null || true

  for _ in $(seq 1 10); do
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$PID_FILE"
      echo "Arrêté."
      return 0
    fi
    sleep 1
  done

  echo "Le processus ne s'est pas arrêté proprement, envoi de SIGKILL..."
  kill -9 "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  echo "Arrêté."
}

restart_server() {
  stop_server
  start_server
}

show_logs() {
  ensure_project
  touch "$LOG_FILE"
  tail -f "$LOG_FILE"
}

main() {
  local command="${1:-status}"
  case "$command" in
    start) start_server ;;
    stop) stop_server ;;
    restart) restart_server ;;
    status) show_status ;;
    logs) show_logs ;;
    help|--help|-h) usage ;;
    *)
      echo "Commande inconnue : $command"
      echo
      usage
      exit 1
      ;;
  esac
}

main "$@"
