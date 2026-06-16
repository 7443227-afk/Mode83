from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app import database
from app.proofs.models import VerificationProof


def _maintenant_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ligne_vers_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


class ProofRepository:
    """Persistance SQLite des preuves locales de credentials."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = db_path

    def initialiser_connexion(self) -> sqlite3.Connection:
        """Ouvre une connexion et initialise le schéma si nécessaire."""

        return database.init_db_schema(self.db_path)

    def sauvegarder(self, preuve: VerificationProof) -> dict[str, Any]:
        """Insère ou met à jour une preuve locale."""

        conn = self.initialiser_connexion()
        try:
            return sauvegarder_preuve(conn, preuve)
        finally:
            database.close_connection(conn)

    def trouver_par_assertion(self, assertion_id: str) -> dict[str, Any] | None:
        """Retourne la preuve associée à une assertion."""

        conn = self.initialiser_connexion()
        try:
            return trouver_preuve_par_assertion(conn, assertion_id)
        finally:
            database.close_connection(conn)

    def trouver_par_hash(self, credential_hash: str) -> dict[str, Any] | None:
        """Retourne la preuve associée à un hash de credential."""

        conn = self.initialiser_connexion()
        try:
            return trouver_preuve_par_hash(conn, credential_hash)
        finally:
            database.close_connection(conn)

    def mettre_a_jour_statut_ancrage(self, assertion_id: str, anchoring_status: str) -> dict[str, Any] | None:
        """Met à jour le statut d'ancrage résumé d'une preuve locale."""

        conn = self.initialiser_connexion()
        try:
            return mettre_a_jour_statut_ancrage_preuve(conn, assertion_id, anchoring_status)
        finally:
            database.close_connection(conn)


def sauvegarder_preuve(conn: sqlite3.Connection, preuve: VerificationProof) -> dict[str, Any]:
    """Insère ou met à jour une preuve dans une connexion existante."""

    donnees = preuve.to_dict()
    updated_at = _maintenant_iso()
    with conn:
        conn.execute(
            '''
            INSERT INTO credential_proofs (
                assertion_id, proof_version, hash_algorithm, canonicalization,
                credential_hash, canonical_payload, anchoring_status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(assertion_id) DO UPDATE SET
                proof_version = excluded.proof_version,
                hash_algorithm = excluded.hash_algorithm,
                canonicalization = excluded.canonicalization,
                credential_hash = excluded.credential_hash,
                canonical_payload = excluded.canonical_payload,
                anchoring_status = excluded.anchoring_status,
                updated_at = excluded.updated_at
            ''',
            (
                donnees["assertion_id"],
                donnees["proof_version"],
                donnees["hash_algorithm"],
                donnees["canonicalization"],
                donnees["credential_hash"],
                donnees["canonical_payload"],
                donnees["anchoring_status"],
                donnees["created_at"],
                updated_at,
            ),
        )
        conn.commit()

    preuve_stockee = trouver_preuve_par_assertion(conn, preuve.assertion_id)
    if preuve_stockee is None:
        raise RuntimeError("La preuve locale n'a pas pu être relue après sauvegarde.")
    return preuve_stockee


def trouver_preuve_par_assertion(
    conn: sqlite3.Connection,
    assertion_id: str,
) -> dict[str, Any] | None:
    """Recherche une preuve par identifiant d'assertion."""

    cursor = conn.execute(
        "SELECT * FROM credential_proofs WHERE assertion_id = ?",
        (assertion_id,),
    )
    return _ligne_vers_dict(cursor.fetchone())


def trouver_preuve_par_hash(
    conn: sqlite3.Connection,
    credential_hash: str,
) -> dict[str, Any] | None:
    """Recherche une preuve par hash de credential."""

    cursor = conn.execute(
        "SELECT * FROM credential_proofs WHERE credential_hash = ?",
        (credential_hash,),
    )
    return _ligne_vers_dict(cursor.fetchone())


def mettre_a_jour_statut_ancrage_preuve(
    conn: sqlite3.Connection,
    assertion_id: str,
    anchoring_status: str,
) -> dict[str, Any] | None:
    """Met à jour uniquement le statut d'ancrage résumé d'une preuve."""

    with conn:
        conn.execute(
            '''
            UPDATE credential_proofs
            SET anchoring_status = ?,
                updated_at = ?
            WHERE assertion_id = ?
            ''',
            (anchoring_status, _maintenant_iso(), assertion_id),
        )
        conn.commit()
    return trouver_preuve_par_assertion(conn, assertion_id)