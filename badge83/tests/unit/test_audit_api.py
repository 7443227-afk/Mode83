from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app import main
from app.main import AUTH_COOKIE_NAME, _make_auth_cookie, app
from app.proofs.audit import AuditEvent
from app.proofs.audit_repository import AuditRepository


def _client_admin() -> TestClient:
    client = TestClient(app)
    client.cookies.set(AUTH_COOKIE_NAME, _make_auth_cookie("admin"))
    return client


def _sauvegarder_assertion(tmp_path, monkeypatch, assertion_id: str = "audit-api-1") -> str:
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
        "recipient": {"type": "email", "hashed": True, "salt": "sel-test", "identity": "sha256$abc123"},
        "issuedOn": "2026-06-08T10:00:00+00:00",
        "verification": {"type": "HostedBadge", "url": f"https://tests.mode83.local/assertions/{assertion_id}"},
        "badge": "https://tests.mode83.local/badges/blockchain-foundations",
        "issuer": "https://tests.mode83.local/issuers/main",
        "admin_recipient": {"name": "Alice Exemple"},
    }
    (issued_dir / f"{assertion_id}.json").write_text(json.dumps(assertion, ensure_ascii=False), encoding="utf-8")
    return assertion_id


def test_api_audit_requires_authentication():
    client = TestClient(app)

    response = client.get("/api/badges/audit-api-1/audit")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_api_audit_retourne_404_si_badge_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "ISSUED_DIR", tmp_path / "issued")
    monkeypatch.setattr(main, "BAKED_DIR", tmp_path / "baked")
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(tmp_path / "registry.db"))
    client = _client_admin()

    response = client.get("/api/badges/inconnu/audit")

    assert response.status_code == 404
    assert response.json()["detail"] == "Badge introuvable"


def test_api_audit_liste_les_evenements_du_badge(tmp_path, monkeypatch):
    assertion_id = _sauvegarder_assertion(tmp_path, monkeypatch)
    repository = AuditRepository(tmp_path / "registry.db")
    repository.enregistrer(AuditEvent(event_type="credential_issued", assertion_id=assertion_id, actor="system"))
    repository.enregistrer(AuditEvent(event_type="anchoring_completed", assertion_id=assertion_id, actor="admin-ui"))
    client = _client_admin()

    response = client.get(f"/api/badges/{assertion_id}/audit")

    assert response.status_code == 200
    data = response.json()
    assert data["assertion_id"] == assertion_id
    assert data["available"] is True
    assert data["count"] == 2
    assert data["latest_event_type"] == "anchoring_completed"
    assert [event["event_type"] for event in data["items"]] == ["credential_issued", "anchoring_completed"]


def test_api_badge_detail_inclut_le_resume_audit(tmp_path, monkeypatch):
    assertion_id = _sauvegarder_assertion(tmp_path, monkeypatch, "audit-api-detail-1")
    AuditRepository(tmp_path / "registry.db").enregistrer(
        AuditEvent(event_type="proof_created", assertion_id=assertion_id, actor="system")
    )
    client = _client_admin()

    response = client.get(f"/api/badges/{assertion_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["audit"]["available"] is True
    assert data["audit"]["count"] == 1
    assert data["audit"]["items"][0]["event_type"] == "proof_created"