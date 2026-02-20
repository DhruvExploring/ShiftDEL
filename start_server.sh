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

# 4. Start Backend Server
echo "[*] Starting FastAPI Backend on Port $BACKEND_PORT..."
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload &
BACKEND_PID=$!

# 5. Start Frontend Server
echo "[*] Starting Vite Frontend..."
cd frontend
npm run dev -- --port $FRONTEND_PORT &
FRONTEND_PID=$!
cd ..

echo "==========================================="
echo "   Servers Running!"
echo "   Backend:  http://localhost:$BACKEND_PORT"
echo "   Frontend: http://localhost:$FRONTEND_PORT"
echo "   Press Ctrl+C to stop both."
echo "==========================================="

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
