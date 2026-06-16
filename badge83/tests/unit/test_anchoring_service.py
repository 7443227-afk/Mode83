from __future__ import annotations

import pytest

from app.proofs import HashService, VerificationProof
from app.proofs.audit_repository import AuditRepository
from app.proofs.anchoring_providers import EvmAnchoringProvider, MockAnchoringProvider, NoopAnchoringProvider, get_anchoring_provider
from app.proofs.anchoring_repository import AnchoringRepository
from app.proofs.anchoring_service import AnchoringService
from app.proofs.repository import ProofRepository


def _assertion(assertion_id: str = "ancrage-service-1") -> dict:
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
    }


def _sauvegarder_preuve(db_path, assertion_id: str = "ancrage-service-1") -> dict:
    assertion = _assertion(assertion_id)
    hash_service = HashService()
    preuve = VerificationProof(
        assertion_id=assertion_id,
        credential_hash=hash_service.calculer_hash(assertion),
        canonical_payload=hash_service.construire_payload_canonique(assertion),
    )
    return ProofRepository(db_path).sauvegarder(preuve)


def test_mock_provider_retourne_un_ancrage_simule():
    provider = MockAnchoringProvider()

    result = provider.anchor({"id": 7, "credential_hash": "sha256:abcdef1234567890"})

    assert result.status == "anchored"
    assert result.tx_hash == "mock:abcdef1234567890"
    assert result.block_number == 7
    assert result.network == "local-demo"


def test_noop_provider_retourne_un_echec_controle():
    provider = NoopAnchoringProvider()

    result = provider.anchor({"id": 1, "credential_hash": "sha256:abc"})

    assert result.status == "failed"
    assert "Aucun provider" in str(result.error_message)


def test_get_anchoring_provider_retourne_mock_ou_noop():
    assert isinstance(get_anchoring_provider("mock"), MockAnchoringProvider)
    assert isinstance(get_anchoring_provider("evm"), EvmAnchoringProvider)
    assert isinstance(get_anchoring_provider("inconnu"), NoopAnchoringProvider)


def test_demander_ancrage_cree_transaction_queued_et_audit(tmp_path):
    db_path = tmp_path / "registry.db"
    preuve = _sauvegarder_preuve(db_path)
    service = AnchoringService(db_path)

    transaction = service.demander_ancrage("ancrage-service-1", provider="mock", actor="admin-test")
    evenements = AuditRepository(db_path).lister_par_assertion("ancrage-service-1")

    assert transaction["status"] == "queued"
    assert transaction["provider"] == "mock"
    assert transaction["network"] == "local-demo"
    assert transaction["credential_hash"] == preuve["credential_hash"]
    assert evenements[-1]["event_type"] == "anchoring_requested"
    assert evenements[-1]["actor"] == "admin-test"


def test_traiter_transaction_mock_passe_de_queued_a_anchored_et_audit(tmp_path):
    db_path = tmp_path / "registry.db"
    _sauvegarder_preuve(db_path, "ancrage-service-2")
    service = AnchoringService(db_path)
    transaction = service.demander_ancrage("ancrage-service-2", provider="mock")

    anchored = service.traiter_transaction(transaction["id"], provider="mock", actor="worker-test")
    evenements = AuditRepository(db_path).lister_par_assertion("ancrage-service-2")

    assert anchored["status"] == "anchored"
    assert anchored["attempts"] == 1
    assert anchored["tx_hash"].startswith("mock:")
    assert anchored["block_number"] == transaction["id"]
    assert [event["event_type"] for event in evenements][-2:] == [
        "anchoring_requested",
        "anchoring_completed",
    ]
    assert evenements[-1]["actor"] == "worker-test"
    assert evenements[-1]["payload"]["status"] == "anchored"
    assert ProofRepository(db_path).trouver_par_assertion("ancrage-service-2")["anchoring_status"] == "anchored"


def test_traiter_transaction_noop_enregistre_un_echec(tmp_path):
    db_path = tmp_path / "registry.db"
    _sauvegarder_preuve(db_path, "ancrage-service-3")
    service = AnchoringService(db_path)
    transaction = service.demander_ancrage("ancrage-service-3", provider="noop")

    failed = service.traiter_transaction(transaction["id"], provider="noop")
    evenements = AuditRepository(db_path).lister_par_assertion("ancrage-service-3")

    assert failed["status"] == "failed"
    assert failed["attempts"] == 1
    assert "Aucun provider" in failed["error_message"]
    assert evenements[-1]["event_type"] == "anchoring_failed"


def test_echec_evm_necrase_pas_un_ancrage_mock_reussi(tmp_path):
    db_path = tmp_path / "registry.db"
    assertion_id = "ancrage-service-mixed"
    _sauvegarder_preuve(db_path, assertion_id)
    service = AnchoringService(db_path)

    mock_transaction = service.demander_ancrage(assertion_id, provider="mock")
    service.traiter_transaction(mock_transaction["id"], provider="mock")
    evm_transaction = service.demander_ancrage(assertion_id, provider="evm")
    failed = service.traiter_transaction(evm_transaction["id"], provider="evm")
    proof = ProofRepository(db_path).trouver_par_assertion(assertion_id)

    assert failed["status"] == "failed"
    assert failed["provider"] == "evm"
    assert proof["anchoring_status"] == "anchored"


def test_traiter_file_traite_les_transactions_queued(tmp_path):
    db_path = tmp_path / "registry.db"
    _sauvegarder_preuve(db_path, "ancrage-service-4")
    _sauvegarder_preuve(db_path, "ancrage-service-5")
    service = AnchoringService(db_path)
    service.demander_ancrage("ancrage-service-4", provider="mock")
    service.demander_ancrage("ancrage-service-5", provider="mock")

    resultats = service.traiter_file(provider="mock", limit=10)
    queued = AnchoringRepository(db_path).lister_par_statut("queued")

    assert len(resultats) == 2
    assert all(transaction["status"] == "anchored" for transaction in resultats)
    assert queued == []


def test_demander_ancrage_sans_preuve_retourne_erreur_controlee(tmp_path):
    service = AnchoringService(tmp_path / "registry.db")

    with pytest.raises(ValueError, match="Preuve locale introuvable"):
        service.demander_ancrage("badge-inconnu", provider="mock")