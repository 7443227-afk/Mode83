from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import AUTH_COOKIE_NAME, _make_auth_cookie, app
from app.proofs import HashService, VerificationProof
from app.proofs.repository import ProofRepository


def _client_admin() -> TestClient:
    client = TestClient(app)
    client.cookies.set(AUTH_COOKIE_NAME, _make_auth_cookie("admin"))
    return client


def _construire_preuve(assertion_id: str = "preuve-api-1") -> VerificationProof:
    assertion = {
        "id": f"https://tests.mode83.local/assertions/{assertion_id}",
        "type": "Assertion",
        "recipient": {
            "type": "email",
            "hashed": True,
            "salt": "sel-test",
            "identity": "sha256$abc123",
        },
        "badge": "https://tests.mode83.local/badges/blockchain-foundations",
        "issuer": "https://tests.mode83.local/issuers/main",
        "issuedOn": "2026-06-08T10:00:00+00:00",
        "verification": {
            "type": "HostedBadge",
            "url": f"https://tests.mode83.local/assertions/{assertion_id}",
        },
    }
    service = HashService()
    return VerificationProof(
        assertion_id=assertion_id,
        credential_hash=service.calculer_hash(assertion),
        canonical_payload=service.construire_payload_canonique(assertion),
    )


def test_api_proof_requires_authentication():
    client = TestClient(app)

    response = client.get("/api/badges/preuve-api-1/proof")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_api_proof_retourne_la_preuve_locale(tmp_path, monkeypatch):
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(tmp_path / "registry.db"))
    preuve = _construire_preuve()
    ProofRepository(tmp_path / "registry.db").sauvegarder(preuve)
    client = _client_admin()

    response = client.get("/api/badges/preuve-api-1/proof")

    assert response.status_code == 200
    data = response.json()
    assert data["assertion_id"] == "preuve-api-1"
    assert data["proof_version"] == "badge83-proof-v1"
    assert data["hash_algorithm"] == "sha256"
    assert data["canonicalization"] == "json-rfc8785-lite-v1"
    assert data["credential_hash"].startswith("sha256:")
    assert data["anchoring_status"] == "not_requested"
    assert "canonical_payload" not in data


def test_api_proof_retourne_404_si_preuve_absente(tmp_path, monkeypatch):
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(tmp_path / "registry.db"))
    client = _client_admin()

    response = client.get("/api/badges/inconnue/proof")

    assert response.status_code == 404
    assert response.json()["detail"] == "Preuve locale introuvable"