import json

class PendingRegistraionRepository:
    def __init__(self,redis_client):
        self.client = redis_client

    def _key(self,email):
        return f"pending_reg:{email}"
    
    def save(self,email, data , ttl=300):
        key = self._key(email)
        self.client.setex(key,ttl,json.dumps(data))

    def get(self,email):
        key = self._key(email)
        raw = self.client.get(key)
        return json.loads(raw) if raw else None
    
    def delete(self, email):
        key = self._key(email)
        self.client.delete(key)
