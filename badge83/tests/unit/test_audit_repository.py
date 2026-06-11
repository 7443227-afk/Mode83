from __future__ import annotations

import pytest

from app import database
from app.proofs.audit import AuditEvent
from app.proofs.audit_repository import AuditRepository, enregistrer_evenement, lister_evenements_par_assertion


def test_initialisation_cree_la_table_audit_events(tmp_path):
    db_path = tmp_path / "registry.db"
    conn = database.init_db_schema(db_path)
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'audit_events'")
        row = cursor.fetchone()
    finally:
        database.close_connection(conn)

    assert row is not None


def test_repository_enregistre_et_liste_un_evenement_audit(tmp_path):
    repository = AuditRepository(tmp_path / "registry.db")

    evenement = repository.enregistrer(
        AuditEvent(
            event_type="credential_issued",
            actor="system",
            assertion_id="badge-1",
            credential_hash="sha256:abc123",
            payload={"issuance_mode": "json"},
        )
    )
    evenements = repository.lister_par_assertion("badge-1")

    assert evenement["event_type"] == "credential_issued"
    assert evenement["assertion_id"] == "badge-1"
    assert evenement["credential_hash"] == "sha256:abc123"
    assert evenement["payload"] == {"issuance_mode": "json"}
    assert len(evenements) == 1
    assert evenements[0]["event_id"] == evenement["event_id"]


def test_fonctions_audit_sur_connexion_existante(tmp_path):
    conn = database.init_db_schema(tmp_path / "registry.db")
    try:
        enregistrer_evenement(
            conn,
            AuditEvent(
                event_type="proof_created",
                assertion_id="badge-2",
                credential_hash="sha256:def456",
            ),
        )
        evenements = lister_evenements_par_assertion(conn, "badge-2")
    finally:
        database.close_connection(conn)

    assert len(evenements) == 1
    assert evenements[0]["event_type"] == "proof_created"


def test_audit_event_refuse_un_type_inconnu():
    with pytest.raises(ValueError):
        AuditEvent(event_type="evenement_inconnu")