from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.application import app


def mount_fake_composer(mock):
    def fake_composer():
        return mock
    return fake_composer


def test_client(app = app) -> TestClient:
    test_client = TestClient(app)
    return test_client


def client(mock: AsyncMock, overrides) -> TestClient:
    app.dependency_overrides[overrides] = mount_fake_composer(mock=mock)
    app.user_middleware.clear()
    app.middleware_stack = app.build_middleware_stack()
    return test_client(app=app)
