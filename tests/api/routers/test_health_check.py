from tests.api.routers import test_client


def test_health_check():

    api = test_client()

    response = api.get("/health")
    assert response.status_code == 200

    body = response.json()

    assert "message" in body
