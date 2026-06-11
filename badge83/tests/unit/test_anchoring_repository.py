from __future__ import annotations

from app import database
from app.proofs.anchoring import AnchoringTransaction, normaliser_statut_ancrage
from app.proofs.anchoring_repository import (
    AnchoringRepository,
    changer_statut_transaction,
    enregistrer_transaction,
    lister_transactions_par_statut,
)


def test_initialisation_cree_la_table_anchoring_transactions(tmp_path):
    conn = database.init_db_schema(tmp_path / "registry.db")
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'anchoring_transactions'"
        )
        row = cursor.fetchone()
    finally:
        database.close_connection(conn)

    assert row is not None


def test_repository_enqueue_une_transaction_queued(tmp_path):
    repository = AnchoringRepository(tmp_path / "registry.db")

    transaction = repository.enqueue(
        assertion_id="badge-1",
        credential_hash="sha256:abc123",
        provider="mock",
        network="local-demo",
    )

    assert transaction["assertion_id"] == "badge-1"
    assert transaction["credential_hash"] == "sha256:abc123"
    assert transaction["provider"] == "mock"
    assert transaction["network"] == "local-demo"
    assert transaction["status"] == "queued"
    assert transaction["attempts"] == 0


def test_repository_change_les_statuts_du_cycle_local(tmp_path):
    repository = AnchoringRepository(tmp_path / "registry.db")
    transaction = repository.enqueue("badge-1", "sha256:abc123", provider="mock")

    pending = repository.changer_statut(transaction["id"], "pending", increment_attempts=True)
    anchored = repository.changer_statut(
        transaction["id"],
        "anchored",
        tx_hash="mock-tx-1",
        block_number=42,
    )

    assert pending["status"] == "pending"
    assert pending["attempts"] == 1
    assert anchored["status"] == "anchored"
    assert anchored["tx_hash"] == "mock-tx-1"
    assert anchored["block_number"] == 42


def test_repository_liste_les_transactions_par_statut(tmp_path):
    repository = AnchoringRepository(tmp_path / "registry.db")
    repository.enqueue("badge-1", "sha256:abc123", provider="mock")
    transaction = repository.enqueue("badge-2", "sha256:def456", provider="mock")
    repository.changer_statut(transaction["id"], "failed", error_message="provider indisponible")

    queued = repository.lister_par_statut("queued")
    failed = repository.lister_par_statut("failed")

    assert [item["assertion_id"] for item in queued] == ["badge-1"]
    assert [item["assertion_id"] for item in failed] == ["badge-2"]
    assert failed[0]["error_message"] == "provider indisponible"


def test_fonctions_sur_connexion_existante_et_retry_scheduled(tmp_path):
    conn = database.init_db_schema(tmp_path / "registry.db")
    try:
        transaction = enregistrer_transaction(
            conn,
            AnchoringTransaction(assertion_id="badge-1", credential_hash="sha256:abc123", provider="noop"),
        )
        changer_statut_transaction(
            conn,
            transaction["id"],
            "retry_scheduled",
            error_message="rpc timeout",
            next_retry_at="2026-06-11T10:00:00+00:00",
            increment_attempts=True,
        )
        retry = lister_transactions_par_statut(conn, "retry_scheduled")
    finally:
        database.close_connection(conn)

    assert len(retry) == 1
    assert retry[0]["status"] == "retry_scheduled"
    assert retry[0]["attempts"] == 1
    assert retry[0]["next_retry_at"] == "2026-06-11T10:00:00+00:00"


def test_statut_inconnu_est_normalise_en_queued():
    assert normaliser_statut_ancrage("statut_inconnu") == "queued"