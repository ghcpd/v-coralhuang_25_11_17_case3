import redis
from fixes.config import config
import logging

logger = logging.getLogger(__name__)

try:
    import fakeredis
except Exception:
    fakeredis = None

class RedisClient:
    def __init__(self, url=None):
        self.url = url or config.REDIS_URL
        self._client = None
        # attempt to create a real redis connection; if it fails, use fakeredis as fallback
        try:
            self._client = redis.Redis.from_url(self.url, socket_connect_timeout=1, socket_timeout=1)
            # test connection
            self._client.ping()
        except Exception:
            logger.warning("Real Redis not available; falling back to fakeredis or in-memory store")
            if fakeredis is not None:
                self._client = fakeredis.FakeRedis()
            else:
                # simple in-memory fallback (dict)
                self._client = _InMemoryRedis()

    def get(self, key):
        try:
            return self._client.get(key)
        except Exception as e:
            logger.exception("Redis get failed")
            return None

    def set(self, key, value, ex=None):
        try:
            return self._client.set(key, value, ex=ex)
        except Exception as e:
            logger.exception("Redis set failed")
            return False

    def setex(self, key, seconds, value):
        try:
            return self._client.setex(key, seconds, value)
        except Exception as e:
            logger.exception("Redis setex failed")
            return False

class _InMemoryRedis:
    def __init__(self):
        self._store = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value, ex=None):
        self._store[key] = value
        return True

    def setex(self, key, seconds, value):
        self._store[key] = value
        return True

# factory
redis_client = RedisClient()
