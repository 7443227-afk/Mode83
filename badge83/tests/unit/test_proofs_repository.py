from __future__ import annotations

from app import database
from app.proofs import HashService, VerificationProof
from app.proofs.repository import ProofRepository, sauvegarder_preuve, trouver_preuve_par_assertion


def construire_assertion_minimale() -> dict:
    return {
        "id": "https://tests.mode83.local/assertions/preuve-1",
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
            "url": "https://tests.mode83.local/assertions/preuve-1",
        },
    }


def construire_preuve(assertion_id: str = "preuve-1") -> VerificationProof:
    service = HashService()
    assertion = construire_assertion_minimale()
    return VerificationProof(
        assertion_id=assertion_id,
        credential_hash=service.calculer_hash(assertion),
        canonical_payload=service.construire_payload_canonique(assertion),
    )


def test_initialisation_cree_la_table_credential_proofs(tmp_path):
    db_path = tmp_path / "registry.db"
    conn = database.init_db_schema(db_path)
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'credential_proofs'"
        )
        row = cursor.fetchone()
    finally:
        database.close_connection(conn)

    assert row is not None


def test_repository_sauvegarde_et_retrouve_une_preuve(tmp_path):
    repository = ProofRepository(tmp_path / "registry.db")
    preuve = construire_preuve()

    stockee = repository.sauvegarder(preuve)
    retrouvee = repository.trouver_par_assertion("preuve-1")

    assert stockee["assertion_id"] == "preuve-1"
    assert retrouvee is not None
    assert retrouvee["credential_hash"] == preuve.credential_hash
    assert retrouvee["anchoring_status"] == "not_requested"


def test_repository_retrouve_une_preuve_par_hash(tmp_path):
    repository = ProofRepository(tmp_path / "registry.db")
    preuve = construire_preuve()
    repository.sauvegarder(preuve)

    retrouvee = repository.trouver_par_hash(preuve.credential_hash)

    assert retrouvee is not None
    assert retrouvee["assertion_id"] == "preuve-1"


def test_sauvegarde_preuve_met_a_jour_la_ligne_existante(tmp_path):
    db_path = tmp_path / "registry.db"
    conn = database.init_db_schema(db_path)
    try:
        preuve = construire_preuve()
        sauvegarder_preuve(conn, preuve)

        preuve_modifiee = VerificationProof(
            assertion_id="preuve-1",
            credential_hash="sha256:" + "b" * 64,
            canonical_payload='{"version":"modifiee"}',
            anchoring_status="queued",
        )
        sauvegarder_preuve(conn, preuve_modifiee)

        retrouvee = trouver_preuve_par_assertion(conn, "preuve-1")
    finally:
        database.close_connection(conn)

    assert retrouvee is not None
    assert retrouvee["credential_hash"] == "sha256:" + "b" * 64
    assert retrouvee["canonical_payload"] == '{"version":"modifiee"}'
    assert retrouvee["anchoring_status"] == "queued"


def test_repository_retourne_none_si_preuve_absente(tmp_path):
    repository = ProofRepository(tmp_path / "registry.db")

    assert repository.trouver_par_assertion("inconnue") is None
    assert repository.trouver_par_hash("sha256:" + "0" * 64) is None