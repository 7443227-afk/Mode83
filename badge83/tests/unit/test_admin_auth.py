from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_admin_api_requires_authentication():
    client = TestClient(app)

    response = client.get("/api/badges")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_badge_constructor_requires_authentication():
    client = TestClient(app)

    response = client.get("/badge-constructor/templates")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_public_verify_endpoint_remains_available():
    client = TestClient(app)

    response = client.get("/verify/non-existent-badge-id")

    assert response.status_code == 200
    assert response.json()["valid"] is False


def test_public_openbadges_endpoint_remains_available():
    client = TestClient(app)

    response = client.get("/issuers/main")

    assert response.status_code in {200, 404}
    assert response.status_code != 401