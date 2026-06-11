from __future__ import annotations

from app import database
from app.proofs.revocation import CredentialRevocation, normaliser_raison_revocation
from app.proofs.revocation_repository import (
    RevocationRepository,
    est_revoque,
    sauvegarder_revocation,
    trouver_revocation,
)


def test_initialisation_cree_la_table_credential_revocations(tmp_path):
    db_path = tmp_path / "registry.db"
    conn = database.init_db_schema(db_path)
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'credential_revocations'"
        )
        row = cursor.fetchone()
    finally:
        database.close_connection(conn)

    assert row is not None


def test_repository_revoque_et_retrouve_une_assertion(tmp_path):
    repository = RevocationRepository(tmp_path / "registry.db")

    revocation = repository.revoquer(
        "badge-1",
        reason_category="erreur_emission",
        actor="admin",
    )
    retrouvee = repository.trouver("badge-1")

    assert revocation["assertion_id"] == "badge-1"
    assert revocation["revoked"] is True
    assert revocation["reason_category"] == "erreur_emission"
    assert revocation["actor"] == "admin"
    assert retrouvee is not None
    assert retrouvee["revoked"] is True


def test_repository_est_revoque_retourne_true_pour_badge_revoque(tmp_path):
    repository = RevocationRepository(tmp_path / "registry.db")
    repository.revoquer("badge-1", reason_category="fraude", actor="admin")

    assert repository.est_revoque("badge-1") is True


def test_repository_est_revoque_retourne_false_pour_badge_inconnu(tmp_path):
    repository = RevocationRepository(tmp_path / "registry.db")

    assert repository.est_revoque("badge-inconnu") is False


def test_sauvegarde_revocation_met_a_jour_la_ligne_existante(tmp_path):
    db_path = tmp_path / "registry.db"
    conn = database.init_db_schema(db_path)
    try:
        sauvegarder_revocation(
            conn,
            CredentialRevocation(
                assertion_id="badge-1",
                reason_category="erreur_emission",
                actor="admin-1",
            ),
        )
        sauvegarder_revocation(
            conn,
            CredentialRevocation(
                assertion_id="badge-1",
                reason_category="demande_titulaire",
                actor="admin-2",
            ),
        )

        retrouvee = trouver_revocation(conn, "badge-1")
        statut = est_revoque(conn, "badge-1")
    finally:
        database.close_connection(conn)

    assert retrouvee is not None
    assert retrouvee["reason_category"] == "demande_titulaire"
    assert retrouvee["actor"] == "admin-2"
    assert statut is True


def test_raison_revocation_inconnue_est_normalisee_en_autre():
    assert normaliser_raison_revocation("raison_libre") == "autre"
    assert normaliser_raison_revocation(None) == "autre"