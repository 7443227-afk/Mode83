#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/home/ubuntu/projects/Mode83/badge83"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
APP_MODULE="app.main:app"
PID_FILE="$PROJECT_DIR/server.pid"
LOG_FILE="$PROJECT_DIR/server.log"

DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"
DEFAULT_BASE_URL="http://mode83.ddns.net"
DEFAULT_SEARCH_PEPPER="badge83-dev-search-pepper"

HOST="${BADGE83_HOST:-$DEFAULT_HOST}"
PORT="${BADGE83_PORT:-$DEFAULT_PORT}"
BASE_URL="${BADGE83_BASE_URL:-$DEFAULT_BASE_URL}"
SEARCH_PEPPER="${BADGE83_SEARCH_PEPPER:-$DEFAULT_SEARCH_PEPPER}"

usage() {
  cat <<USAGE
Badge83 server manager

Usage:
  ./badge83.sh start
  ./badge83.sh stop
  ./badge83.sh restart
  ./badge83.sh status
  ./badge83.sh logs

Optional environment variables:
  BADGE83_HOST      Host to bind (default: $DEFAULT_HOST)
  BADGE83_PORT      Port to bind (default: $DEFAULT_PORT)
  BADGE83_BASE_URL  Public base URL embedded in badges (default: $DEFAULT_BASE_URL)
  BADGE83_SEARCH_PEPPER  Stable pepper for admin search hashes

Examples:
  ./badge83.sh start
  BADGE83_BASE_URL=http://mode83.ddns.net ./badge83.sh restart
  BADGE83_PORT=8010 BADGE83_BASE_URL=http://mode83.ddns.net:8010 ./badge83.sh start
USAGE
}

ensure_project() {
  cd "$PROJECT_DIR"
  if [ ! -x "$VENV_PYTHON" ]; then
    echo "Error: virtualenv python not found at $VENV_PYTHON"
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
    echo "Status     : RUNNING"
    echo "PID        : $pid"
    echo "Bind       : $HOST:$PORT"
    echo "Base URL   : $BASE_URL"
    echo "PID file   : $PID_FILE"
    echo "Log file   : $LOG_FILE"
    ss -ltnp 2>/dev/null | grep ":$PORT" || true
  else
    echo "Status     : STOPPED"
    echo "Bind       : $HOST:$PORT"
    echo "Base URL   : $BASE_URL"
    echo "PID file   : $PID_FILE"
    echo "Log file   : $LOG_FILE"
  fi
}

start_server() {
  ensure_project
  local pid
  if pid="$(running_pid)"; then
    echo "Badge83 is already running (PID $pid)."
    show_status
    return 0
  fi

  echo "Starting Badge83..."
  echo "- Host     : $HOST"
  echo "- Port     : $PORT"
  echo "- Base URL : $BASE_URL"

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
    echo "Started. PID: $effective_pid"
    show_status
  else
    echo "Failed to start Badge83. Last log lines:"
    tail -n 20 "$LOG_FILE" || true
    exit 1
  fi
}

stop_server() {
  ensure_project
  local pid
  if ! pid="$(running_pid)"; then
    echo "Badge83 is not running."
    rm -f "$PID_FILE"
    return 0
  fi

  echo "Stopping Badge83 (PID $pid)..."
  kill "$pid" 2>/dev/null || true

  for _ in $(seq 1 10); do
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$PID_FILE"
      echo "Stopped."
      return 0
    fi
    sleep 1
  done

  echo "Process did not stop gracefully, sending SIGKILL..."
  kill -9 "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  echo "Stopped."
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
      echo "Unknown command: $command"
      echo
      usage
      exit 1
      ;;
  esac
}

main "$@"
