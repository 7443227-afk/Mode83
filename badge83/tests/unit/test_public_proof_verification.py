from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.proofs import HashService, VerificationProof
from app.proofs.repository import ProofRepository


def _assertion(assertion_id: str = "preuve-publique-1") -> dict:
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "@language": "fr-FR",
        "id": f"https://tests.mode83.local/assertions/{assertion_id}",
        "type": "Assertion",
        "url": f"https://tests.mode83.local/assertions/{assertion_id}",
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


def _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, assertion: dict) -> str:
    assertion_id = assertion["id"].rstrip("/").split("/")[-1]
    issued_dir = tmp_path / "issued"
    baked_dir = tmp_path / "baked"
    registry_db = tmp_path / "registry.db"
    issued_dir.mkdir(parents=True, exist_ok=True)
    baked_dir.mkdir(parents=True, exist_ok=True)
    (issued_dir / f"{assertion_id}.json").write_text(
        json.dumps(assertion, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "ISSUED_DIR", issued_dir)
    monkeypatch.setattr(main, "BAKED_DIR", baked_dir)
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(registry_db))

    hash_service = HashService()
    preuve = VerificationProof(
        assertion_id=assertion_id,
        credential_hash=hash_service.calculer_hash(assertion),
        canonical_payload=hash_service.construire_payload_canonique(assertion),
    )
    ProofRepository(registry_db).sauvegarder(preuve)
    return assertion_id


def test_page_verification_complete_affiche_la_preuve_locale(tmp_path, monkeypatch):
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, _assertion())
    client = TestClient(app)

    response = client.get(f"/verify/badge/{assertion_id}")

    assert response.status_code == 200
    assert "Preuve locale cohérente" in response.text
    assert "sha256:" in response.text


def test_page_verification_qr_affiche_la_preuve_locale(tmp_path, monkeypatch):
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, _assertion())
    client = TestClient(app)

    response = client.get(f"/verify/qr/{assertion_id}")

    assert response.status_code == 200
    assert "Preuve locale Badge83" in response.text
    assert "Preuve locale cohérente" in response.text


def test_page_verification_signale_une_preuve_incoherente(tmp_path, monkeypatch):
    assertion = _assertion("preuve-publique-2")
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, assertion)
    json_path = tmp_path / "issued" / f"{assertion_id}.json"
    assertion["issuedOn"] = "2026-06-09T10:00:00+00:00"
    json_path.write_text(json.dumps(assertion, ensure_ascii=False), encoding="utf-8")
    client = TestClient(app)

    response = client.get(f"/verify/badge/{assertion_id}")

    assert response.status_code == 200
    assert "Preuve locale incohérente" in response.text