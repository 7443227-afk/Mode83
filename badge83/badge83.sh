#!/bin/bash

# Config
PROJECT_DIR="/home/ubuntu/projects/Mode83/badge83"
VENV="$PROJECT_DIR/.venv/bin/activate"
BASE_URL="http://mode83.ddns.net"
PORT=8000
PID_FILE="$PROJECT_DIR/server.pid"

cd "$PROJECT_DIR"

status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        return 0 # Running
    else
        return 1 # Stopped
    fi
}

start_server() {
    echo "Starting Badge83 on $BASE_URL..."
    source "$VENV"
    export BADGE83_BASE_URL="$BASE_URL"
    nohup uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload > server.log 2>&1 &
    echo $! > "$PID_FILE"
    echo "Server started. PID: $(cat "$PID_FILE")"
}

stop_server() {
    PID=$(cat "$PID_FILE" 2>/dev/null)
    # Fallback to lsof if PID file missing but port taken
    [ -z "$PID" ] && PID=$(lsof -t -i:$PORT)
    
    if [ ! -z "$PID" ]; then
        echo "Stopping server (PID $PID)..."
        kill $PID
        [ -f "$PID_FILE" ] && rm "$PID_FILE"
        echo "Stopped."
    else
        echo "Server not running."
    fi
}

# Clear screen for better UI
clear
echo "--- Badge83 Manager ---"

if status; then
    echo "Status: RUNNING (PID $(cat "$PID_FILE"))"
    echo "URL: $BASE_URL"
    echo ""
    echo "1) Stop server"
    echo "2) Restart server"
    echo "3) View logs (tail)"
    echo "4) Exit"
    read -p "Action: " choice
    case "$choice" in
        1) stop_server ;;
        2) stop_server; sleep 2; start_server ;;
        3) tail -f server.log ;;
        *) exit 0 ;;
    esac
else
    echo "Status: STOPPED"
    echo ""
    echo "1) Start server"
    echo "2) Exit"
    read -p "Action: " choice
    case "$choice" in
        1) start_server ;;
        *) exit 0 ;;
    esac
fi
