from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app import main
from app.main import AUTH_COOKIE_NAME, _make_auth_cookie, app


def _client_admin() -> TestClient:
    client = TestClient(app)
    client.cookies.set(AUTH_COOKIE_NAME, _make_auth_cookie("admin"))
    return client


def _sauvegarder_assertion(tmp_path, monkeypatch, assertion_id: str = "revocation-api-1") -> str:
    issued_dir = tmp_path / "issued"
    baked_dir = tmp_path / "baked"
    registry_db = tmp_path / "registry.db"
    issued_dir.mkdir(parents=True, exist_ok=True)
    baked_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(main, "ISSUED_DIR", issued_dir)
    monkeypatch.setattr(main, "BAKED_DIR", baked_dir)
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(registry_db))

    assertion = {
        "@context": "https://w3id.org/openbadges/v2",
        "id": f"https://tests.mode83.local/assertions/{assertion_id}",
        "type": "Assertion",
        "recipient": {
            "type": "email",
            "hashed": True,
            "salt": "sel-test",
            "identity": "sha256$abc123",
        },
        "issuedOn": "2026-06-08T10:00:00+00:00",
        "verification": {
            "type": "HostedBadge",
            "url": f"https://tests.mode83.local/assertions/{assertion_id}",
        },
        "badge": "https://tests.mode83.local/badges/blockchain-foundations",
        "issuer": "https://tests.mode83.local/issuers/main",
        "admin_recipient": {"name": "Alice Exemple"},
    }
    (issued_dir / f"{assertion_id}.json").write_text(
        json.dumps(assertion, ensure_ascii=False),
        encoding="utf-8",
    )
    return assertion_id


def test_api_revoke_requires_authentication():
    client = TestClient(app)

    response = client.post("/api/badges/revocation-api-1/revoke")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_api_get_revocation_requires_authentication():
    client = TestClient(app)

    response = client.get("/api/badges/revocation-api-1/revocation")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_api_revoke_retourne_404_si_badge_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "ISSUED_DIR", tmp_path / "issued")
    monkeypatch.setattr(main, "BAKED_DIR", tmp_path / "baked")
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(tmp_path / "registry.db"))
    client = _client_admin()

    response = client.post("/api/badges/inconnu/revoke", json={"reason_category": "fraude"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Badge introuvable"


def test_api_revoke_marque_un_badge_comme_revoque(tmp_path, monkeypatch):
    assertion_id = _sauvegarder_assertion(tmp_path, monkeypatch)
    client = _client_admin()

    response = client.post(
        f"/api/badges/{assertion_id}/revoke",
        json={"reason_category": "demande_titulaire", "actor": "admin-test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["assertion_id"] == assertion_id
    assert data["revoked"] is True
    assert data["reason_category"] == "demande_titulaire"
    assert data["actor"] == "admin-test"


def test_api_get_revocation_retourne_le_statut_public(tmp_path, monkeypatch):
    assertion_id = _sauvegarder_assertion(tmp_path, monkeypatch)
    client = _client_admin()
    client.post(f"/api/badges/{assertion_id}/revoke", json={"reason_category": "fraude"})

    response = client.get(f"/api/badges/{assertion_id}/revocation")

    assert response.status_code == 200
    data = response.json()
    assert data["assertion_id"] == assertion_id
    assert data["status"] == "revoked"
    assert data["public_label"] == "révoqué"
    assert data["reason_category"] == "fraude"