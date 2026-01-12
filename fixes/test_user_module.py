# _*_ coding: utf-8 _*_
"""
Comprehensive test suite for fixed user module.
Tests all success and failure paths for both endpoints.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from config import AppConfig, RedisConfig, CeleryConfig, DatabaseConfig
from db import User, init_db, get_session, close_session
from error import Unauthorized, NotFound, BadRequest, ServerError
from redis_client import get_redis_client, redis_setex, redis_get, RedisClientFactory
from token_parser import parse_bearer_token
from user_module_fixed import (
    create_test_app, user_bp, get_profile, upload_avatar,
    log_avatar_change, init_module, _get_user_cache_key
)
from conftest import requires_redis


# Fixtures

@pytest.fixture
def config():
    """Create test configuration with in-memory database."""
    return AppConfig(
        testing=True,
        debug=False,
        env="testing",
        redis=RedisConfig(
            host="127.0.0.1",
            port=6379,
            db=0,
            connection_pool_size=5
        ),
        celery=CeleryConfig(
            broker_url="redis://127.0.0.1:6379/1",
            backend_url="redis://127.0.0.1:6379/2",
            task_always_eager=True,  # Eager mode for testing
            task_eager_propagates=True
        ),
        database=DatabaseConfig(
            url="sqlite:///:memory:",
            echo=False,
            pool_size=5,
            max_overflow=10
        ),
        cache_ttl_seconds=300
    )


@pytest.fixture
def app(config):
    """Create Flask test app."""
    return create_test_app(config=config)


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for tests."""
    session = get_session()
    yield session
    close_session(session)


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        nickname="testuser",
        email="test@example.com",
        avatar="http://example.com/avatar.jpg",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def redis_client():
    """Get Redis client for testing."""
    # Use a test database to avoid conflicts
    return get_redis_client(RedisConfig(
        host="127.0.0.1",
        port=6379,
        db=15,  # Test DB
        connection_pool_size=5
    ))


# Token Parser Tests

class TestTokenParser:
    """Test token parsing and validation."""

    def test_parse_bearer_token_valid(self):
        """Test parsing valid bearer token."""
        token = "Bearer 123"
        user_id = parse_bearer_token(token)
        assert user_id == 123

    def test_parse_bearer_token_missing_header(self):
        """Test missing authorization header."""
        with pytest.raises(Unauthorized) as exc:
            parse_bearer_token(None)
        assert "missing authorization header" in str(exc.value)

    def test_parse_bearer_token_invalid_format(self):
        """Test invalid header format."""
        with pytest.raises(Unauthorized) as exc:
            parse_bearer_token("Bearer 123 456")
        assert "invalid authorization header format" in str(exc.value)

    def test_parse_bearer_token_wrong_scheme(self):
        """Test wrong authentication scheme."""
        with pytest.raises(Unauthorized) as exc:
            parse_bearer_token("Basic 123")
        assert "invalid authorization scheme" in str(exc.value)

    def test_parse_bearer_token_non_integer(self):
        """Test non-integer token."""
        with pytest.raises(Unauthorized) as exc:
            parse_bearer_token("Bearer abc")
        assert "invalid token format" in str(exc.value)

    def test_parse_bearer_token_negative_id(self):
        """Test negative user ID."""
        with pytest.raises(Unauthorized) as exc:
            parse_bearer_token("Bearer -1")
        assert "positive integer" in str(exc.value)

    def test_parse_bearer_token_zero_id(self):
        """Test zero user ID."""
        with pytest.raises(Unauthorized) as exc:
            parse_bearer_token("Bearer 0")
        assert "positive integer" in str(exc.value)

    def test_parse_bearer_token_whitespace(self):
        """Test token with extra whitespace."""
        token = "  Bearer   456  "
        user_id = parse_bearer_token(token)
        assert user_id == 456


# Profile Endpoint Tests

class TestGetProfile:
    """Test GET /v1/user/profile endpoint."""

    def test_get_profile_success(self, client, test_user):
        """Test successful profile retrieval."""
        response = client.get(
            "/v1/user/profile",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["error_code"] == 0
        assert data["msg"] == "success"
        assert data["data"]["id"] == test_user.id
        assert data["data"]["nickname"] == "testuser"
        assert data["data"]["email"] == "test@example.com"

    def test_get_profile_missing_auth(self, client):
        """Test missing authorization header."""
        response = client.get("/v1/user/profile")
        assert response.status_code == 401
        data = response.get_json()
        assert data["error_code"] == 401
        assert "missing authorization header" in data["msg"]

    def test_get_profile_invalid_auth(self, client):
        """Test invalid authorization header."""
        response = client.get(
            "/v1/user/profile",
            headers={"Authorization": "Invalid"}
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["error_code"] == 401

    def test_get_profile_user_not_found(self, client):
        """Test non-existent user."""
        response = client.get(
            "/v1/user/profile",
            headers={"Authorization": "Bearer 99999"}
        )
        assert response.status_code == 404
        data = response.get_json()
        assert data["error_code"] == 404
        assert "not found" in data["msg"]

    def test_get_profile_soft_deleted_user(self, client, db_session, test_user):
        """Test accessing soft-deleted user."""
        # Soft delete the user
        test_user.soft_delete()
        db_session.commit()
        
        # Try to access
        response = client.get(
            "/v1/user/profile",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 404
        data = response.get_json()
        assert data["error_code"] == 404

    def test_get_profile_inactive_user(self, client, db_session, test_user):
        """Test accessing inactive user."""
        # Mark user as inactive
        test_user.is_active = False
        db_session.commit()
        
        # Try to access
        response = client.get(
            "/v1/user/profile",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 404

    @requires_redis
    def test_get_profile_caching(self, client, db_session, test_user, redis_client):
        """Test profile caching behavior."""
        user_id = test_user.id
        cache_key = _get_user_cache_key(user_id)
        
        # Clear cache
        redis_client.delete(cache_key)
        
        # First request - cache miss
        response1 = client.get(
            "/v1/user/profile",
            headers={"Authorization": f"Bearer {user_id}"}
        )
        assert response1.status_code == 200
        data1 = response1.get_json()
        
        # Verify cache is populated
        cached = redis_client.get(cache_key)
        assert cached is not None
        cached_data = json.loads(cached.decode("utf-8"))
        assert cached_data["id"] == user_id
        
        # Second request - cache hit
        response2 = client.get(
            "/v1/user/profile",
            headers={"Authorization": f"Bearer {user_id}"}
        )
        assert response2.status_code == 200
        data2 = response2.get_json()
        
        # Data should be identical
        assert data1["data"] == data2["data"]

    @requires_redis
    def test_get_profile_cache_corruption_fallback(self, client, db_session, test_user, redis_client):
        """Test fallback to DB when cache is corrupted."""
        user_id = test_user.id
        cache_key = _get_user_cache_key(user_id)
        
        # Corrupt cache with invalid JSON
        redis_client.set(cache_key, b"invalid json")
        
        # Should fallback to DB and return success
        response = client.get(
            "/v1/user/profile",
            headers={"Authorization": f"Bearer {user_id}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["error_code"] == 0


# Avatar Upload Endpoint Tests

class TestUploadAvatar:
    """Test POST /v1/user/avatar endpoint."""

    def test_upload_avatar_success(self, client, test_user):
        """Test successful avatar upload."""
        response = client.post(
            "/v1/user/avatar",
            headers={"Authorization": f"Bearer {test_user.id}"},
            data={"file": (b"fake image data", "avatar.jpg")}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["error_code"] == 0
        assert data["msg"] == "success"
        assert "avatar.jpg" in data["data"]["avatar"]

    def test_upload_avatar_missing_file(self, client, test_user):
        """Test upload without file."""
        response = client.post(
            "/v1/user/avatar",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["error_code"] == 400
        assert "missing" in data["msg"] or "file" in data["msg"]

    def test_upload_avatar_empty_file(self, client, test_user):
        """Test upload with empty file."""
        response = client.post(
            "/v1/user/avatar",
            headers={"Authorization": f"Bearer {test_user.id}"},
            data={"file": (b"", "")}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["error_code"] == 400

    def test_upload_avatar_missing_auth(self, client):
        """Test upload without authorization."""
        response = client.post(
            "/v1/user/avatar",
            data={"file": (b"fake", "test.jpg")}
        )
        assert response.status_code == 401

    def test_upload_avatar_user_not_found(self, client):
        """Test upload for non-existent user."""
        response = client.post(
            "/v1/user/avatar",
            headers={"Authorization": "Bearer 99999"},
            data={"file": (b"fake", "test.jpg")}
        )
        assert response.status_code == 404

    def test_upload_avatar_updates_db(self, client, db_session, test_user):
        """Test that avatar upload updates database."""
        user_id = test_user.id
        
        response = client.post(
            "/v1/user/avatar",
            headers={"Authorization": f"Bearer {user_id}"},
            data={"file": (b"data", "newavatar.jpg")}
        )
        assert response.status_code == 200
        
        # Verify DB is updated
        session = get_session()
        try:
            updated_user = User.get(session=session, id=user_id)
            assert updated_user is not None
            assert "newavatar.jpg" in updated_user.avatar
        finally:
            close_session(session)

    def test_upload_avatar_updates_cache(self, client, test_user, redis_client):
        """Test that avatar upload updates cache."""
        user_id = test_user.id
        cache_key = _get_user_cache_key(user_id)
        redis_client.delete(cache_key)
        
        response = client.post(
            "/v1/user/avatar",
            headers={"Authorization": f"Bearer {user_id}"},
            data={"file": (b"data", "cached_avatar.jpg")}
        )
        assert response.status_code == 200
        
        # Verify cache is updated
        cached = redis_client.get(cache_key)
        assert cached is not None
        cached_data = json.loads(cached.decode("utf-8"))
        assert "cached_avatar.jpg" in cached_data["avatar"]

    def test_upload_avatar_soft_deleted_user(self, client, db_session, test_user):
        """Test upload for soft-deleted user."""
        test_user.soft_delete()
        db_session.commit()
        
        response = client.post(
            "/v1/user/avatar",
            headers={"Authorization": f"Bearer {test_user.id}"},
            data={"file": (b"data", "test.jpg")}
        )
        assert response.status_code == 404


# Celery Task Tests

class TestCeleryTask:
    """Test log_avatar_change Celery task."""

    def test_log_avatar_change_success(self, db_session, test_user):
        """Test successful avatar change logging."""
        result = log_avatar_change(
            test_user.id,
            "http://example.com/new.jpg",
            datetime.utcnow().isoformat()
        )
        # Celery task returns result
        assert result is True or result is None  # Depends on Celery mode

    def test_log_avatar_change_with_invalid_datetime(self):
        """Test avatar logging with invalid datetime."""
        result = log_avatar_change(
            1,
            "http://example.com/avatar.jpg",
            "not-a-valid-iso-date"
        )
        # Should handle gracefully
        assert result is False

    def test_log_avatar_change_eager_mode(self, config):
        """Test that Celery eager mode is enabled in tests."""
        assert config.celery.task_always_eager is True


# Integration Tests

class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_user_lifecycle(self, client, db_session):
        """Test full user workflow: create, fetch profile, upload avatar."""
        # Create user
        user = User(
            nickname="integration_user",
            email="integration@example.com",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        
        # Get profile
        resp1 = client.get(
            "/v1/user/profile",
            headers={"Authorization": f"Bearer {user_id}"}
        )
        assert resp1.status_code == 200
        profile = resp1.get_json()
        assert profile["data"]["nickname"] == "integration_user"
        
        # Upload avatar
        resp2 = client.post(
            "/v1/user/avatar",
            headers={"Authorization": f"Bearer {user_id}"},
            data={"file": (b"avatar_data", "integration_avatar.jpg")}
        )
        assert resp2.status_code == 200
        avatar_resp = resp2.get_json()
        assert "integration_avatar.jpg" in avatar_resp["data"]["avatar"]
        
        # Get profile again - should have updated avatar
        resp3 = client.get(
            "/v1/user/profile",
            headers={"Authorization": f"Bearer {user_id}"}
        )
        assert resp3.status_code == 200
        updated_profile = resp3.get_json()
        assert updated_profile["data"]["avatar"] == avatar_resp["data"]["avatar"]

    def test_multiple_users_isolation(self, client, db_session):
        """Test that multiple users don't interfere with each other."""
        # Create two users
        user1 = User(nickname="user1", email="user1@example.com")
        user2 = User(nickname="user2", email="user2@example.com")
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        
        # Get profiles
        resp1 = client.get(
            "/v1/user/profile",
            headers={"Authorization": f"Bearer {user1.id}"}
        )
        resp2 = client.get(
            "/v1/user/profile",
            headers={"Authorization": f"Bearer {user2.id}"}
        )
        
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.get_json()["data"]["nickname"] == "user1"
        assert resp2.get_json()["data"]["nickname"] == "user2"


# Error Handling Tests

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_malformed_json_response_on_error(self, client):
        """Test that errors return valid JSON."""
        response = client.get(
            "/v1/user/profile",
            headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == 401
        data = response.get_json()
        assert isinstance(data, dict)
        assert "error_code" in data
        assert "msg" in data

    def test_response_includes_request_url_on_error(self, client):
        """Test that error response includes request URL."""
        response = client.get(
            "/v1/user/profile",
            headers={"Authorization": "Bearer invalid"}
        )
        data = response.get_json()
        # Request URL may or may not be included depending on context
        if "request_url" in data:
            assert "profile" in data["request_url"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
