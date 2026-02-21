import httpx
import logging

logger = logging.getLogger("relay-client")

class EphemeralRelayClient:
    def __init__(self, relay_url="http://localhost:8000"):
        self.base_url = relay_url

    async def create_session(self, session_id: str, encrypted_metadata: str):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/create-session",
                json={"session_id": session_id, "encrypted_metadata": encrypted_metadata}
            )
            return resp.status_code == 200

    async def verify_session(self, session_id: str):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/verify-session",
                json={"session_id": session_id}
            )
            if resp.status_code == 200:
                return resp.json()
            return None

    async def release_key(self, session_id: str, auth_token: str):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/release-key",
                json={"session_id": session_id, "auth_token": auth_token}
            )
            try:
                data = resp.json()
            except:
                data = {"error": resp.text}
            return resp.status_code == 200, data

    async def mark_delivered(self, session_id: str):
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/mark-delivered",
                json={"session_id": session_id}
            )

    async def destroy_session(self, session_id: str):
        async with httpx.AsyncClient() as client:
            await client.delete(f"{self.base_url}/destroy-session?session_id={session_id}")
