#!/bin/bash

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Trap SIGINT and SIGTERM to kill background processes
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}
trap cleanup SIGINT SIGTERM

echo "==========================================="
echo "   ShifDEL - Unified Server Starter"
echo "==========================================="

# 1. Cleanup: Kill any running/stuck server instances
echo "[*] Cleaning up old processes..."
pkill -f "uvicorn" || true
lsof -ti :$BACKEND_PORT | xargs kill -9 2>/dev/null || true
lsof -ti :8080 | xargs kill -9 2>/dev/null || true
lsof -ti :$FRONTEND_PORT | xargs kill -9 2>/dev/null || true

# 2. Activate Virtual Environment & Check Backend
if [ -d "faceenv" ]; then
    echo "[*] Activating faceenv..."
    source faceenv/bin/activate
else
    echo "CRITICAL ERROR: 'faceenv' directory not found."
    exit 1
fi

echo "[*] Checking Backend Dependencies..."
python3 -c "import dlib; import face_recognition; print('Dependencies OK')" || {
    echo "WARNING: dlib or face_recognition missing/broken in faceenv. Backend will run in Mock Mode."
}

# 3. Check Frontend Dependencies
echo "[*] Checking Frontend..."
if [ ! -d "frontend/node_modules" ]; then
    echo "WARNING: 'frontend/node_modules' not found. Installing dependencies..."
    cd frontend && npm install && cd ..
fi

# 3.5 Check & Start Redis (Required for Ephemeral Pipeline)
if ! command -v redis-cli &> /dev/null; then
    echo "CRITICAL ERROR: 'redis-server' not found. Please install Redis."
    exit 1
fi

if ! redis-cli ping &>/dev/null; then
    echo "[*] Redis is not running. Attempting to start redis-server..."
    redis-server --daemonize yes
    sleep 2
    if ! redis-cli ping &>/dev/null; then
        echo "CRITICAL ERROR: Failed to start Redis server."
        exit 1
    fi
    echo "[*] Redis started successfully."
else
    echo "[*] Redis is already running."
fi

# 4. Start Internal Backend Server
echo "[*] Starting Internal Backend on Port 8080..."
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!

# 5. Start Security Relay Server
echo "[*] Starting Security Relay on Port $BACKEND_PORT..."
python3 -m uvicorn relay.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload &
RELAY_PID=$!

# Wait for Relay to be ready
echo "[*] Waiting for Security Relay to initialize..."
for i in {1..10}; do
    if curl -s http://localhost:$BACKEND_PORT/docs &>/dev/null; then
        echo "[*] Security Relay is UP."
        break
    fi
    if [ $i -eq 10 ]; then
        echo "WARNING: Security Relay is taking a long time to start or failed."
    fi
    sleep 1
done

# 6. Start Vite Frontend
echo "[*] Starting Vite Frontend..."
cd frontend
npm run dev -- --port $FRONTEND_PORT &
FRONTEND_PID=$!
cd ..

echo "==========================================="
echo "   Servers Running!"
echo "   Relay:    http://localhost:$BACKEND_PORT (Public Gateway)"
echo "   Internal: http://localhost:8080 (Isolated)"
echo "   Frontend: http://localhost:$FRONTEND_PORT"
echo "   Press Ctrl+C to stop all."
echo "==========================================="

# Wait for processes
wait $BACKEND_PID $RELAY_PID $FRONTEND_PID
