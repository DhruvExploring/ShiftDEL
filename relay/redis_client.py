import redis
import json
import os

class RedisSessionStore:
    def __init__(self):
        # Defaulting to localhost, can be overridden via env
        self.r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )

    def create_session(self, session_id: str, encrypted_metadata: str, ttl=600):
        data = {
            "metadata": encrypted_metadata,
            "fails": 0,
            "status": "active"
        }
        self.r.hset(f"session:{session_id}", mapping=data)
        self.r.expire(f"session:{session_id}", ttl)

    def get_session(self, session_id: str):
        return self.r.hgetall(f"session:{session_id}")

    def increment_fail(self, session_id: str):
        fails = self.r.hincrby(f"session:{session_id}", "fails", 1)
        if fails >= 3:
            self.destroy_session(session_id)
        return fails

    def mark_delivered(self, session_id: str):
        self.r.hset(f"session:{session_id}", "status", "delivered")
        # Auto-delete on successful delivery (immediate)
        self.destroy_session(session_id)

    def destroy_session(self, session_id: str):
        self.r.delete(f"session:{session_id}")
