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

DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="8000"
DEFAULT_PUBLIC_SCHEME="https"
DEFAULT_PUBLIC_HOST="mode83.ddns.net"
DEFAULT_PUBLIC_PORT="443"
DEFAULT_SEARCH_PEPPER="badge83-dev-search-pepper"
DEFAULT_ENABLE_FIREWALL_MANAGEMENT="false"
DEFAULT_PUBLIC_HTTP_PORT="80"
DEFAULT_PUBLIC_HTTPS_PORT="443"
DEFAULT_AUTH_USERNAME="admin"
DEFAULT_AUTH_PASSWORD="admin"
DEFAULT_AUTH_SECRET="badge83-dev-auth-secret-change-me"

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
PUBLIC_PORT="${BADGE83_PUBLIC_PORT:-$DEFAULT_PUBLIC_PORT}"
ENABLE_FIREWALL_MANAGEMENT="${BADGE83_ENABLE_FIREWALL_MANAGEMENT:-$DEFAULT_ENABLE_FIREWALL_MANAGEMENT}"
PUBLIC_HTTP_PORT="${BADGE83_PUBLIC_HTTP_PORT:-$DEFAULT_PUBLIC_HTTP_PORT}"
PUBLIC_HTTPS_PORT="${BADGE83_PUBLIC_HTTPS_PORT:-$DEFAULT_PUBLIC_HTTPS_PORT}"
if [ -n "${BADGE83_BASE_URL:-}" ]; then
  BASE_URL="${BADGE83_BASE_URL%/}"
elif { [ "$PUBLIC_SCHEME" = "http" ] && [ "$PUBLIC_PORT" = "80" ]; } || { [ "$PUBLIC_SCHEME" = "https" ] && [ "$PUBLIC_PORT" = "443" ]; }; then
  BASE_URL="$PUBLIC_SCHEME://$PUBLIC_HOST"
else
  BASE_URL="$PUBLIC_SCHEME://$PUBLIC_HOST:$PUBLIC_PORT"
fi
SEARCH_PEPPER="${BADGE83_SEARCH_PEPPER:-$DEFAULT_SEARCH_PEPPER}"
AUTH_USERNAME="${BADGE83_AUTH_USERNAME:-$DEFAULT_AUTH_USERNAME}"
AUTH_PASSWORD="${BADGE83_AUTH_PASSWORD:-$DEFAULT_AUTH_PASSWORD}"
AUTH_SECRET="${BADGE83_AUTH_SECRET:-$DEFAULT_AUTH_SECRET}"

usage() {
  cat <<USAGE
Gestionnaire du serveur Badge83

Utilisation :
  ./badge83.sh start
  ./badge83.sh stop
  ./badge83.sh restart
  ./badge83.sh status
  ./badge83.sh logs
  ./badge83.sh firewall-open
  ./badge83.sh firewall-close

Fichier de configuration :
  $CONFIG_FILE

Variables d'environnement optionnelles :
  BADGE83_HOST      Hôte d'écoute interne (défaut : $DEFAULT_HOST)
  BADGE83_PORT      Port d'écoute interne (défaut : $DEFAULT_PORT)
  BADGE83_BASE_URL  URL publique canonique intégrée dans les badges
  BADGE83_PUBLIC_SCHEME  Schéma public si BADGE83_BASE_URL n'est pas défini (défaut : $DEFAULT_PUBLIC_SCHEME)
  BADGE83_PUBLIC_HOST    Nom d'hôte public si BADGE83_BASE_URL n'est pas défini (défaut : $DEFAULT_PUBLIC_HOST)
  BADGE83_PUBLIC_PORT    Port public si BADGE83_BASE_URL n'est pas défini (défaut : $DEFAULT_PUBLIC_PORT)
  BADGE83_SEARCH_PEPPER  Pepper stable pour les hash de recherche admin
  BADGE83_AUTH_USERNAME  Identifiant de la page de connexion Nginx auth_request
  BADGE83_AUTH_PASSWORD  Mot de passe de la page de connexion Nginx auth_request
  BADGE83_AUTH_SECRET    Secret HMAC pour signer la cookie de session
  BADGE83_ENABLE_FIREWALL_MANAGEMENT  true pour ouvrir/fermer 80/443 via iptables pendant start/stop
  BADGE83_PUBLIC_HTTP_PORT            Port HTTP public géré par firewall-open/firewall-close (défaut : 80)
  BADGE83_PUBLIC_HTTPS_PORT           Port HTTPS public géré par firewall-open/firewall-close (défaut : 443)

Exemples :
  ./badge83.sh start
  BADGE83_BASE_URL=https://mode83.ddns.net ./badge83.sh restart
  ./badge83.sh firewall-open
  BADGE83_ENABLE_FIREWALL_MANAGEMENT=true ./badge83.sh start
USAGE
}

is_true() {
  case "${1:-}" in
    true|TRUE|1|yes|YES|y|Y|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

require_sudo_for_firewall() {
  if ! command -v sudo >/dev/null 2>&1; then
    echo "Erreur : sudo est requis pour modifier iptables."
    exit 1
  fi
  if ! command -v iptables >/dev/null 2>&1; then
    echo "Erreur : iptables est introuvable."
    exit 1
  fi
}

iptables_allow_port() {
  local port="$1"
  require_sudo_for_firewall
  if sudo iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null; then
    echo "Firewall : le port $port/tcp est déjà autorisé."
  else
    sudo iptables -I INPUT -p tcp --dport "$port" -j ACCEPT
    echo "Firewall : port $port/tcp autorisé."
  fi
}

iptables_close_port() {
  local port="$1"
  require_sudo_for_firewall
  while sudo iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null; do
    sudo iptables -D INPUT -p tcp --dport "$port" -j ACCEPT
    echo "Firewall : règle ACCEPT supprimée pour $port/tcp."
  done
}

firewall_open() {
  echo "Ouverture contrôlée des ports publics HTTP/HTTPS."
  echo "Important : le port interne Badge83 ($PORT/tcp) ne sera pas ouvert."
  iptables_allow_port "$PUBLIC_HTTP_PORT"
  iptables_allow_port "$PUBLIC_HTTPS_PORT"
}

firewall_close() {
  echo "Fermeture contrôlée des ports publics HTTP/HTTPS."
  iptables_close_port "$PUBLIC_HTTP_PORT"
  iptables_close_port "$PUBLIC_HTTPS_PORT"
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
    echo "Firewall   : gestion automatique = $ENABLE_FIREWALL_MANAGEMENT ; ports publics = $PUBLIC_HTTP_PORT,$PUBLIC_HTTPS_PORT"
    echo "Fichier PID: $PID_FILE"
    echo "Fichier log: $LOG_FILE"
    ss -ltnp 2>/dev/null | grep ":$PORT" || true
  else
    echo "Statut     : ARRÊTÉ"
    echo "Écoute     : $HOST:$PORT"
    echo "URL de base: $BASE_URL"
    echo "Firewall   : gestion automatique = $ENABLE_FIREWALL_MANAGEMENT ; ports publics = $PUBLIC_HTTP_PORT,$PUBLIC_HTTPS_PORT"
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
  if [ "$HOST" != "127.0.0.1" ] && [ "$HOST" != "localhost" ]; then
    echo "AVERTISSEMENT : BADGE83_HOST=$HOST. Le backend peut être exposé directement. La valeur recommandée est 127.0.0.1."
  fi

  if is_true "$ENABLE_FIREWALL_MANAGEMENT"; then
    firewall_open
  fi

  export BADGE83_BASE_URL="$BASE_URL"
  export BADGE83_HOST="$HOST"
  export BADGE83_PORT="$PORT"
  export BADGE83_SEARCH_PEPPER="$SEARCH_PEPPER"
  export BADGE83_AUTH_USERNAME="$AUTH_USERNAME"
  export BADGE83_AUTH_PASSWORD="$AUTH_PASSWORD"
  export BADGE83_AUTH_SECRET="$AUTH_SECRET"
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
      if is_true "$ENABLE_FIREWALL_MANAGEMENT"; then
        firewall_close
      fi
      return 0
    fi
    sleep 1
  done

  echo "Le processus ne s'est pas arrêté proprement, envoi de SIGKILL..."
  kill -9 "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  echo "Arrêté."
  if is_true "$ENABLE_FIREWALL_MANAGEMENT"; then
    firewall_close
  fi
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
    firewall-open) firewall_open ;;
    firewall-close) firewall_close ;;
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
