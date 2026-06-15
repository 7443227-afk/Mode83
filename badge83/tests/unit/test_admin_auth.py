from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import AUTH_COOKIE_NAME, _make_auth_cookie, app


def _client_admin() -> TestClient:
    client = TestClient(app)
    client.cookies.set(AUTH_COOKIE_NAME, _make_auth_cookie("admin"))
    return client


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


def test_admin_index_expose_le_bouton_ancrage_local():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="anchorLocalBtn"' in response.text
    assert "Demander un ancrage local" in response.text
    assert "/anchor" in response.text
    assert "provider: 'mock'" in response.text


def test_admin_index_expose_le_bouton_ancrage_blockchain_evm_distinct():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="anchorEvmBtn"' in response.text
    assert "Demander un ancrage blockchain réel" in response.text
    assert "Request real blockchain anchoring" in response.text
    assert "Запросить реальный blockchain-анкеринг" in response.text
    assert "requestRealEvmAnchoring" in response.text
    assert "provider: 'evm'" in response.text


def test_admin_index_expose_option_ancrage_local_apres_emission():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="issueAnchorLocal"' in response.text
    assert "Demander aussi un ancrage local mock après émission" in response.text
    assert "requestLocalMockAnchoring" in response.text
    assert "maybeAnchorIssuedBadge" in response.text


def test_admin_index_expose_audit_trail_dans_inspecteur():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert "Audit trail" in response.text
    assert "renderAuditAdminSummary" in response.text
    assert "/audit" in response.text


def test_admin_index_expose_resume_ancrage_apres_emission():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert "renderIssueAnchoringResultSummary" in response.text
    assert "Ancrage local confirmé" in response.text
    assert "Ancrage local non confirmé" in response.text