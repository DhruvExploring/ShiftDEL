#!/bin/bash

# 1. Cleanup: Kill any running/stuck server instances
echo "Stopping old server instances..."
pkill -f "uvicorn" || true
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# 2. Activate Virtual Environment
if [ -d "faceenv" ]; then
    echo "Activating faceenv..."
    source faceenv/bin/activate
else
    echo "CRITICAL ERROR: 'faceenv' directory not found."
    echo "Please ensure you are in the project root."
    exit 1
fi

# 3. Verify Dependencies
echo "Verifying dlib installation..."
python3 -c "import dlib; import face_recognition; print('Dependencies OK')" || {
    echo "ERROR: dlib or face_recognition missing in faceenv!"
    exit 1
}

# 4. Start Backend Server
echo "Starting FastAPI Backend..."
# Use exec to replace shell with python process (better signal handling)
exec python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
