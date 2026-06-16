from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.proofs import HashService, VerificationProof
from app.proofs.anchoring_repository import AnchoringRepository
from app.proofs.repository import ProofRepository
from app.proofs.revocation_repository import RevocationRepository


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


def test_pages_verification_affichent_un_badge_revoque(tmp_path, monkeypatch):
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, _assertion("preuve-revoquee-1"))
    RevocationRepository(tmp_path / "registry.db").revoquer(
        assertion_id,
        reason_category="erreur_emission",
        actor="admin-test",
    )
    client = TestClient(app)

    full_response = client.get(f"/verify/badge/{assertion_id}")
    qr_response = client.get(f"/verify/qr/{assertion_id}")

    assert full_response.status_code == 200
    assert qr_response.status_code == 200
    assert "Statut credential" in full_response.text
    assert "Credential révoqué" in full_response.text
    assert "erreur_emission" in full_response.text
    assert "Statut : révoqué" in qr_response.text


def test_pages_verification_affichent_un_ancrage_mock_confirme(tmp_path, monkeypatch):
    monkeypatch.setenv("BADGE83_EVM_EXPLORER_TX_URL_TEMPLATE", "https://explorer.test/tx/{tx_hash}")
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, _assertion("preuve-ancree-1"))
    repository = AnchoringRepository(tmp_path / "registry.db")
    transaction = repository.enqueue(
        assertion_id=assertion_id,
        credential_hash="sha256:abc123",
        provider="mock",
        network="local-demo",
    )
    repository.changer_statut(
        transaction["id"],
        "anchored",
        tx_hash="mock:abc123",
        block_number=1,
    )
    client = TestClient(app)

    full_response = client.get(f"/verify/badge/{assertion_id}")
    qr_response = client.get(f"/verify/qr/{assertion_id}")

    assert full_response.status_code == 200
    assert qr_response.status_code == 200
    assert "Ancrage confirmé" in full_response.text
    assert "mock:abc123" in full_response.text
    assert "https://explorer.test/tx/mock:abc123" not in full_response.text
    assert "Ancrage : anchored" in qr_response.text


def test_url_explorer_evm_refuse_un_template_non_http(monkeypatch):
    monkeypatch.setenv("BADGE83_EVM_EXPLORER_TX_URL_TEMPLATE", "javascript:alert('{tx_hash}')")

    assert main._build_evm_explorer_tx_url("0xabc123", "evm") is None


def test_pages_verification_affichent_la_verification_blockchain_evm(tmp_path, monkeypatch):
    monkeypatch.setenv("BADGE83_EVM_EXPLORER_TX_URL_TEMPLATE", "https://explorer.test/tx/{tx_hash}")
    assertion = _assertion("preuve-evm-verifiee-1")
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, assertion)
    proof = ProofRepository(tmp_path / "registry.db").trouver_par_assertion(assertion_id)
    repository = AnchoringRepository(tmp_path / "registry.db")
    transaction = repository.enqueue(
        assertion_id=assertion_id,
        credential_hash=proof["credential_hash"],
        provider="evm",
        network="hardhat-unit",
    )
    repository.changer_statut(
        transaction["id"],
        "anchored",
        tx_hash="0xabc123",
        block_number=42,
    )
    monkeypatch.setattr(
        main.EvmAnchoringProvider,
        "verifier_hash_ancre",
        lambda self, credential_hash: {
            "available": True,
            "verified": True,
            "status": "verified",
            "provider": "evm",
            "network": "hardhat-unit",
            "error_message": None,
        },
    )
    client = TestClient(app)

    full_response = client.get(f"/verify/badge/{assertion_id}")
    qr_response = client.get(f"/verify/qr/{assertion_id}")

    assert full_response.status_code == 200
    assert qr_response.status_code == 200
    assert "Vérification blockchain publique" in full_response.text
    assert "Hash confirmé sur blockchain" in full_response.text
    assert "0xabc123" in full_response.text
    assert "https://explorer.test/tx/0xabc123" in full_response.text
    assert "Bloc" in full_response.text
    assert "Vérification blockchain publique" in qr_response.text
    assert "Hash confirmé sur blockchain" in qr_response.text
    assert "https://explorer.test/tx/0xabc123" in qr_response.text


def test_pages_verification_separent_mock_et_evm_meme_si_mock_est_plus_recent(tmp_path, monkeypatch):
    monkeypatch.setenv("BADGE83_EVM_EXPLORER_TX_URL_TEMPLATE", "https://explorer.test/tx/{tx_hash}")
    assertion = _assertion("preuve-mock-evm-separes-1")
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, assertion)
    proof = ProofRepository(tmp_path / "registry.db").trouver_par_assertion(assertion_id)
    repository = AnchoringRepository(tmp_path / "registry.db")
    evm_transaction = repository.enqueue(
        assertion_id=assertion_id,
        credential_hash=proof["credential_hash"],
        provider="evm",
        network="hardhat-unit",
    )
    repository.changer_statut(
        evm_transaction["id"],
        "anchored",
        tx_hash="0xevm123",
        block_number=42,
    )
    mock_transaction = repository.enqueue(
        assertion_id=assertion_id,
        credential_hash=proof["credential_hash"],
        provider="mock",
        network="local-demo",
    )
    repository.changer_statut(
        mock_transaction["id"],
        "anchored",
        tx_hash="mock:latest",
        block_number=43,
    )
    verifier_calls = []
    monkeypatch.setattr(
        main.EvmAnchoringProvider,
        "verifier_hash_ancre",
        lambda self, credential_hash: verifier_calls.append(credential_hash) or {
            "available": True,
            "verified": True,
            "status": "verified",
            "provider": "evm",
            "network": "hardhat-unit",
            "error_message": None,
        },
    )
    client = TestClient(app)

    full_response = client.get(f"/verify/badge/{assertion_id}")
    qr_response = client.get(f"/verify/qr/{assertion_id}")

    assert full_response.status_code == 200
    assert qr_response.status_code == 200
    assert "Ancrage local" in full_response.text
    assert "mock:latest" in full_response.text
    assert "Ancrage blockchain EVM" in full_response.text
    assert "0xevm123" in full_response.text
    assert "https://explorer.test/tx/0xevm123" in full_response.text
    assert "Hash confirmé sur blockchain" in full_response.text
    assert "Ancrage local" in qr_response.text
    assert "mock:latest" in qr_response.text
    assert "Ancrage blockchain EVM" in qr_response.text
    assert "0xevm123" in qr_response.text
    assert "https://explorer.test/tx/0xevm123" in qr_response.text
    assert "Hash confirmé sur blockchain" in qr_response.text
    assert verifier_calls == [proof["credential_hash"], proof["credential_hash"]]


def test_statut_global_reste_confirme_si_evm_echoue_apres_mock(tmp_path, monkeypatch):
    assertion = _assertion("preuve-mock-confirme-evm-echec-1")
    assertion_id = _sauvegarder_assertion_et_preuve(tmp_path, monkeypatch, assertion)
    proof = ProofRepository(tmp_path / "registry.db").trouver_par_assertion(assertion_id)
    repository = AnchoringRepository(tmp_path / "registry.db")
    mock_transaction = repository.enqueue(
        assertion_id=assertion_id,
        credential_hash=proof["credential_hash"],
        provider="mock",
        network="local-demo",
    )
    repository.changer_statut(
        mock_transaction["id"],
        "anchored",
        tx_hash="mock:ok",
        block_number=1,
    )
    evm_transaction = repository.enqueue(
        assertion_id=assertion_id,
        credential_hash=proof["credential_hash"],
        provider="evm",
        network="hardhat-unit",
    )
    repository.changer_statut(
        evm_transaction["id"],
        "failed",
        error_message="Configuration EVM incomplète.",
    )

    status = main._build_anchoring_status(assertion_id)

    assert status["status"] == "anchored"
    assert status["tone"] == "success"
    assert status["mock"]["status"] == "anchored"
    assert status["evm"]["status"] == "failed"
