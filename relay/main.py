from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("relay-server")

app = FastAPI(title="ShiftDEL Security Relay")

# Backend configuration
INTERNAL_BACKEND_URL = "http://localhost:8080"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
