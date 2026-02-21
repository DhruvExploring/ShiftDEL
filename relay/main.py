from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import redis
import time
import jwt
import httpx
import logging
from uuid import UUID
from datetime import datetime, timedelta
from relay.redis_client import RedisSessionStore

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("relay-server")

app = FastAPI(title="ShiftDEL Security Relay")

# Security Config
SECRET_KEY = "ephemeral_secret_change_me" # Hardcoded for demonstration as requested
ALGORITHM = "HS256"
INTERNAL_BACKEND_URL = "http://localhost:8080"

# Redis Store
session_store = RedisSessionStore()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Ephemeral Session Endpoints ---

@app.post("/create-session")
async def create_session(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    encrypted_metadata = data.get("encrypted_metadata")
    
    if not session_id or not encrypted_metadata:
        return Response(status_code=400, content="Missing session info")
    
    try:
        UUID(session_id) # Validate format
        session_store.create_session(session_id, encrypted_metadata)
        logger.info(f"[EPHEMERAL] Session {session_id} created.")
        return {"status": "success"}
    except Exception as e:
        return Response(status_code=400, content=f"Invalid session_id: {str(e)}")

@app.post("/verify-session")
async def verify_session(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    
    session = session_store.get_session(session_id)
    if not session:
        return Response(status_code=404, content="Session expired or invalid")
    
    # Generate temporary JWT for key release
    token = jwt.encode({
        "sub": session_id,
        "exp": datetime.utcnow() + timedelta(minutes=2)
    }, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "encrypted_metadata": session["metadata"],
        "release_token": token
    }

@app.post("/release-key")
async def release_key(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    token = data.get("auth_token")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["sub"] != session_id:
            raise Exception("Token mismatch")
            
        session = session_store.get_session(session_id)
        if not session:
            return Response(status_code=404, content="Session not found")
            
        return {"status": "released"} # The actual key is inside the encrypted metadata held by receiver
    except Exception as e:
        fails = session_store.increment_fail(session_id)
        return Response(
            status_code=401, 
            content=json.dumps({"error": "Invalid authorization", "fails": fails}),
            media_type="application/json"
        )

@app.post("/mark-delivered")
async def mark_delivered(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    session_store.mark_delivered(session_id)
    return {"status": "destroyed"}

@app.delete("/destroy-session")
async def destroy_session(session_id: str):
    session_store.destroy_session(session_id)
    return {"status": "ok"}

# --- Transparent Proxy ---
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def relay_request(request: Request, path: str):
    """
    Transparently proxies all requests to the internal backend.
    """
    url = f"{INTERNAL_BACKEND_URL}/{path}"
    
    # Extract original headers and body
    headers = dict(request.headers)
    # Remove host header to let httpx set the correct one
    headers.pop("host", None)
    
    method = request.method
    content = await request.body()
    params = dict(request.query_params)

    logger.info(f"[RELAY] {method} {url}")

    async with httpx.AsyncClient() as client:
        try:
            # We use a stream to handle potential large files/video streams efficiently
            proxy_response = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                content=content,
                timeout=None
            )
            
            # Return response to frontend
            return Response(
                content=proxy_response.content,
                status_code=proxy_response.status_code,
                headers=dict(proxy_response.headers)
            )
        except Exception as e:
            logger.error(f"[RELAY ERROR] {str(e)}")
            return Response(content="Internal Relay Error", status_code=502)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
