from core.interface.otp_repository_port import OtpRepositoryPort
from core.entities.otp import OtpEntity
from datetime import datetime
import json

class OtpRepository(OtpRepositoryPort):
    def __init__(self, redis_client):
        self.client = redis_client

    def _make_key(self, email, action_type):
        return f"otp:{action_type}:{email}"

    def save_otp(self, otp: OtpEntity):
        key = self._make_key(otp.email, otp.action_type)
        data = otp.__dict__.copy()
        data["expires_at"] = otp.expires_at.isoformat()
        ttl = int((otp.expires_at - datetime.now()).total_seconds())
        self.client.setex(key, ttl, json.dumps(data))

    def get_otp(self, email, action_type):
        key = self._make_key(email, action_type)
        raw = self.client.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        return OtpEntity(
            email=data["email"],
            code=data["code"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            action_type=data["action_type"],
            verified=data["verified"]
        )

    def mark_verified(self, email, action_type):
        key = self._make_key(email, action_type)
        raw = self.client.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        data["verified"] = True
        ttl = self.client.ttl(key)
        self.client.setex(key, ttl, json.dumps(data))

    def delete_otp(self, email, action_type):
        key = self._make_key(email, action_type)
        self.client.delete(key)