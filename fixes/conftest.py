# _*_ coding: utf-8 _*_
"""
Pytest configuration and fixtures.
"""

import pytest
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError


def redis_available():
    """Check if Redis is available."""
    try:
        r = Redis(host="127.0.0.1", port=6379, db=15, socket_timeout=2)
        r.ping()
        return True
    except (RedisConnectionError, Exception):
        return False


# Mark for skipping tests that require Redis
requires_redis = pytest.mark.skipif(
    not redis_available(),
    reason="Redis not available"
)
