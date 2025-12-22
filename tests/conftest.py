"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return {
        "test_db_uri": "mongodb://test:test@localhost:27017/test",
        "test_redis_uri": "redis://localhost:6379/0",
        "test_api_url": "http://localhost:5000",
        "test_frontend_url": "http://localhost:8000",
    }


@pytest.fixture(scope="session")
def mock_user():
    """Mock user fixture for tests."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "is_active": True,
    }