import logging
from typing import Any

from redis import Redis


class CacheClient:
    def __init__(self, redis_url: str | None = None, client: Redis | None = None):
        if client:
            self._client = client
        elif redis_url:
            self._client = Redis.from_url(redis_url, decode_responses=True)
        else:
            raise ValueError("Either redis_url or client must be provided")

    def get(self, key: str) -> Any | None:
        try:
            return self._client.get(key)
        except Exception:
            logging.exception("Redis GET failed for key %s", key)
            return None

    def setex(self, key: str, ttl: int, value: str) -> None:
        try:
            self._client.setex(key, ttl, value)
        except Exception:
            logging.exception("Redis SETEX failed for key %s", key)

    def delete(self, key: str) -> None:
        try:
            self._client.delete(key)
        except Exception:
            logging.exception("Redis DELETE failed for key %s", key)
