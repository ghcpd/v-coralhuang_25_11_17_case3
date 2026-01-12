# _*_ coding: utf-8 _*_
"""
Redis client factory with connection pool and error handling.
"""

import logging
from typing import Optional, Any

from redis import Redis, ConnectionPool
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisClientFactory:
    """Factory for creating and managing Redis clients."""

    _instance: Optional[Redis] = None
    _pool: Optional[ConnectionPool] = None

    @classmethod
    def create(cls, host: str = "127.0.0.1", port: int = 6379, 
              db: int = 0, connection_pool_size: int = 10,
              socket_timeout: int = 5, socket_keepalive: bool = True) -> Redis:
        """
        Create a Redis client with connection pool.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            connection_pool_size: Connection pool size
            socket_timeout: Socket timeout in seconds
            socket_keepalive: Enable TCP keepalive
            
        Returns:
            Redis client instance
        """
        # Create connection pool
        pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            max_connections=connection_pool_size,
            socket_timeout=socket_timeout,
            socket_keepalive=socket_keepalive,
            socket_keepalive_options={
                1: 1,  # TCP_KEEPIDLE
                2: 1,  # TCP_KEEPINTVL
                3: 3,  # TCP_KEEPCNT
            } if socket_keepalive else None,
            decode_responses=False,  # Return bytes by default
        )
        
        client = Redis(connection_pool=pool)
        cls._pool = pool
        cls._instance = client
        return client

    @classmethod
    def get_instance(cls) -> Optional[Redis]:
        """Get singleton Redis instance."""
        return cls._instance

    @classmethod
    def close(cls) -> None:
        """Close Redis connection pool."""
        if cls._pool:
            cls._pool.disconnect()
        if cls._instance:
            cls._instance.close()


def get_redis_client(config) -> Redis:
    """
    Get or create Redis client from config.
    
    Args:
        config: RedisConfig instance
        
    Returns:
        Redis client
    """
    return RedisClientFactory.create(
        host=config.host,
        port=config.port,
        db=config.db,
        connection_pool_size=config.connection_pool_size,
        socket_timeout=config.socket_timeout,
        socket_keepalive=config.socket_keepalive
    )


def redis_get(client: Redis, key: str) -> Optional[bytes]:
    """
    Safely get value from Redis, handling errors gracefully.
    
    Args:
        client: Redis client
        key: Cache key
        
    Returns:
        Cached value or None if not found or error
    """
    try:
        return client.get(key)
    except RedisError as e:
        logger.warning(f"Redis GET error for key {key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Redis GET: {e}")
        return None


def redis_setex(client: Redis, key: str, seconds: int, value: bytes) -> bool:
    """
    Safely set value in Redis with expiration, handling errors gracefully.
    
    Args:
        client: Redis client
        key: Cache key
        seconds: TTL in seconds
        value: Value to cache
        
    Returns:
        True if set successfully, False otherwise
    """
    try:
        client.setex(key, seconds, value)
        return True
    except RedisError as e:
        logger.warning(f"Redis SETEX error for key {key}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Redis SETEX: {e}")
        return False


def redis_delete(client: Redis, key: str) -> bool:
    """
    Safely delete value from Redis, handling errors gracefully.
    
    Args:
        client: Redis client
        key: Cache key
        
    Returns:
        True if deleted, False otherwise
    """
    try:
        result = client.delete(key)
        return result > 0
    except RedisError as e:
        logger.warning(f"Redis DELETE error for key {key}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Redis DELETE: {e}")
        return False
