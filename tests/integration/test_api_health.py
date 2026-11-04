import pytest
from backend.main import root, health_check, app


def test_root_endpoint():
    data = root()
    assert data["name"] == "ReVolt API"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"


def test_health_check_endpoint():
    data = health_check()
    assert "status" in data
    assert "database" in data
    assert "database_name" in data
    assert data["database_name"] == "revolt_db"
    assert "timestamp" in data


def test_cors_middleware_configured():
    middleware_names = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_names
