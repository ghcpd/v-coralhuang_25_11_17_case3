"""Redis helpers that support graceful degradation."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional

from redis import Redis
from redis.exceptions import RedisError


def create_redis_client(redis_url: str) -> Redis:
    """Build a Redis client using a connection pool."""
    return Redis.from_url(redis_url, decode_responses=True, socket_timeout=2)


CacheGetter = Callable[[], Redis]


def _run_safely(client: Redis, operation: Callable[[], Any]) -> Any:
    try:
        return operation()
    except RedisError:
        return None


def get_cached_profile(client: Redis, user_id: int) -> Optional[Dict[str, Any]]:
    def _op():
        payload = client.get(_profile_cache_key(user_id))
        return json.loads(payload) if payload else None

    return _run_safely(client, _op)


def set_cached_profile(client: Redis, user_id: int, data: Dict[str, Any], ttl_seconds: int) -> None:
    payload = json.dumps(data)
    _run_safely(
        client, lambda: client.setex(_profile_cache_key(user_id), ttl_seconds, payload)
    )


def invalidate_profile(client: Redis, user_id: int) -> None:
    _run_safely(client, lambda: client.delete(_profile_cache_key(user_id)))


def _profile_cache_key(user_id: int) -> str:
    return f"user_profile:{user_id}"

