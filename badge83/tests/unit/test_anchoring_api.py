from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app import main
from app.main import AUTH_COOKIE_NAME, _make_auth_cookie, app
from app.proofs import HashService, VerificationProof
from app.proofs.audit_repository import AuditRepository
from app.proofs.repository import ProofRepository


def _client_admin() -> TestClient:
    client = TestClient(app)
    client.cookies.set(AUTH_COOKIE_NAME, _make_auth_cookie("admin"))
    return client


def _assertion(assertion_id: str = "anchoring-api-1") -> dict:
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "id": f"https://tests.mode83.local/assertions/{assertion_id}",
        "type": "Assertion",
        "recipient": {
            "type": "email",
            "hashed": True,
            "salt": "sel-test",
            "identity": "sha256$abc123",
        },
        "issuedOn": "2026-06-11T10:00:00+00:00",
        "verification": {
            "type": "HostedBadge",
            "url": f"https://tests.mode83.local/assertions/{assertion_id}",
        },
        "badge": "https://tests.mode83.local/badges/blockchain-foundations",
        "issuer": "https://tests.mode83.local/issuers/main",
        "admin_recipient": {"name": "Alice Exemple"},
    }


def _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, assertion_id: str = "anchoring-api-1") -> str:
    issued_dir = tmp_path / "issued"
    baked_dir = tmp_path / "baked"
    registry_db = tmp_path / "registry.db"
    issued_dir.mkdir(parents=True, exist_ok=True)
    baked_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(main, "ISSUED_DIR", issued_dir)
    monkeypatch.setattr(main, "BAKED_DIR", baked_dir)
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(registry_db))

    assertion = _assertion(assertion_id)
    (issued_dir / f"{assertion_id}.json").write_text(json.dumps(assertion, ensure_ascii=False), encoding="utf-8")
    hash_service = HashService()
    ProofRepository(registry_db).sauvegarder(
        VerificationProof(
            assertion_id=assertion_id,
            credential_hash=hash_service.calculer_hash(assertion),
            canonical_payload=hash_service.construire_payload_canonique(assertion),
        )
    )
    return assertion_id


def test_api_anchor_requires_authentication():
    client = TestClient(app)

    response = client.post("/api/badges/anchoring-api-1/anchor")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_api_get_anchoring_requires_authentication():
    client = TestClient(app)

    response = client.get("/api/badges/anchoring-api-1/anchoring")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_api_anchor_retourne_404_si_badge_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "ISSUED_DIR", tmp_path / "issued")
    monkeypatch.setattr(main, "BAKED_DIR", tmp_path / "baked")
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(tmp_path / "registry.db"))
    client = _client_admin()

    response = client.post("/api/badges/inconnu/anchor", json={"provider": "mock"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Badge introuvable"


def test_api_anchor_retourne_404_si_preuve_absente(tmp_path, monkeypatch):
    issued_dir = tmp_path / "issued"
    baked_dir = tmp_path / "baked"
    issued_dir.mkdir(parents=True, exist_ok=True)
    baked_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(main, "ISSUED_DIR", issued_dir)
    monkeypatch.setattr(main, "BAKED_DIR", baked_dir)
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(tmp_path / "registry.db"))
    assertion_id = "anchoring-api-no-proof"
    (issued_dir / f"{assertion_id}.json").write_text(json.dumps(_assertion(assertion_id)), encoding="utf-8")
    client = _client_admin()

    response = client.post(f"/api/badges/{assertion_id}/anchor", json={"provider": "mock"})

    assert response.status_code == 404
    assert "Preuve locale introuvable" in response.json()["detail"]


def test_api_anchor_mock_cree_et_traite_un_ancrage(tmp_path, monkeypatch):
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch)
    client = _client_admin()

    response = client.post(
        f"/api/badges/{assertion_id}/anchor",
        json={"provider": "mock", "actor": "admin-anchor"},
    )

    assert response.status_code == 200
    data = response.json()
    transaction = data["transaction"]
    assert data["assertion_id"] == assertion_id
    assert transaction["status"] == "anchored"
    assert transaction["provider"] == "mock"
    assert transaction["network"] == "local-demo"
    assert transaction["tx_hash"].startswith("mock:")
    assert transaction["attempts"] == 1


def test_api_get_anchoring_retourne_les_transactions(tmp_path, monkeypatch):
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, "anchoring-api-2")
    client = _client_admin()
    client.post(f"/api/badges/{assertion_id}/anchor", json={"provider": "mock"})

    response = client.get(f"/api/badges/{assertion_id}/anchoring")


    assert response.status_code == 200
    data = response.json()
    assert data["assertion_id"] == assertion_id
    assert data["latest_status"] == "anchored"
    assert len(data["items"]) == 1
    assert data["items"][0]["status"] == "anchored"


def test_api_anchor_enregistre_les_evenements_audit(tmp_path, monkeypatch):
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, "anchoring-api-audit")
    client = _client_admin()

    response = client.post(
        f"/api/badges/{assertion_id}/anchor",
        json={"provider": "mock", "actor": "admin-anchor"},
    )
    evenements = AuditRepository(tmp_path / "registry.db").lister_par_assertion(assertion_id)

    assert response.status_code == 200
    assert [event["event_type"] for event in evenements][-2:] == [
        "anchoring_requested",
        "anchoring_completed",
    ]
    assert evenements[-1]["actor"] == "admin-anchor"