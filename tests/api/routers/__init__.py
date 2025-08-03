from unittest.mock import AsyncMock

from fastapi.testclient import TestClient


def mount_fake_composer(mock):
    def fake_composer():
        return mock

    return fake_composer


def test_client(app=None) -> TestClient:
    from app.application import app as api_app
    app = app or api_app
    return TestClient(app)


def client(mock: AsyncMock, overrides) -> TestClient:
    from app.application import app as api_app
    app = api_app
    app.dependency_overrides[overrides] = mount_fake_composer(mock=mock)
    app.user_middleware.clear()
    app.middleware_stack = app.build_middleware_stack()
    return test_client(app=app)
