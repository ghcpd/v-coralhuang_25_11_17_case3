import redis
from fixes.config import config
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, url=None):
        self.url = url or config.REDIS_URL
        self._client = redis.Redis.from_url(self.url, socket_connect_timeout=2, socket_timeout=2)

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

# factory
redis_client = RedisClient()
