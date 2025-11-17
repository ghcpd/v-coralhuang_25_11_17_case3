import os

from redis import Redis
from redis.exceptions import RedisError
from redis.connection import ConnectionPool

from .config import config


class RedisFactory:
    def __init__(self, url=None):
        self.url = url or config.REDIS_URL
        self._pool = ConnectionPool.from_url(self.url)
        self._client = None

    def client(self) -> Redis:
        if self._client is None:
            self._client = Redis(connection_pool=self._pool)
        return self._client


# Singleton factory
redis_factory = RedisFactory()


def get_redis_client():
    try:
        return redis_factory.client()
    except RedisError as e:
        # Degrade gracefully: return a dummy in-memory client if redis is not available
        # But we should not import fakeredis at module import unless used
        try:
            import fakeredis
            return fakeredis.FakeStrictRedis()
        except Exception:
            raise
