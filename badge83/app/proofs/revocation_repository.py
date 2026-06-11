from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app import database
from app.proofs.revocation import CredentialRevocation


def _maintenant_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ligne_vers_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if not row:
        return None
    result = dict(row)
    result["revoked"] = bool(result.get("revoked"))
    return result


class RevocationRepository:
    """Persistance SQLite des révocations locales."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = db_path

    def initialiser_connexion(self) -> sqlite3.Connection:
        """Ouvre une connexion et initialise le schéma si nécessaire."""

        return database.init_db_schema(self.db_path)

    def revoquer(
        self,
        assertion_id: str,
        reason_category: str | None = None,
        actor: str | None = None,
    ) -> dict[str, Any]:
        """Marque une assertion comme révoquée."""

        conn = self.initialiser_connexion()
        try:
            revocation = CredentialRevocation(
                assertion_id=assertion_id,
                reason_category=reason_category or "autre",
                actor=actor,
            )
            return sauvegarder_revocation(conn, revocation)
        finally:
            database.close_connection(conn)

    def trouver(self, assertion_id: str) -> dict[str, Any] | None:
        """Retourne la révocation associée à une assertion."""

        conn = self.initialiser_connexion()
        try:
            return trouver_revocation(conn, assertion_id)
        finally:
            database.close_connection(conn)

    def est_revoque(self, assertion_id: str) -> bool:
        """Indique si une assertion est révoquée localement."""

        revocation = self.trouver(assertion_id)
        return bool(revocation and revocation.get("revoked"))


def sauvegarder_revocation(
    conn: sqlite3.Connection,
    revocation: CredentialRevocation,
) -> dict[str, Any]:
    """Insère ou met à jour une révocation dans une connexion existante."""

    donnees = revocation.to_dict()
    updated_at = _maintenant_iso()
    with conn:
        conn.execute(
            '''
            INSERT INTO credential_revocations (
                assertion_id, revoked, reason_category, actor, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(assertion_id) DO UPDATE SET
                revoked = excluded.revoked,
                reason_category = excluded.reason_category,
                actor = excluded.actor,
                updated_at = excluded.updated_at
            ''',
            (
                donnees["assertion_id"],
                donnees["revoked"],
                donnees["reason_category"],
                donnees["actor"],
                donnees["created_at"],
                updated_at,
            ),
        )
        conn.commit()

    revocation_stockee = trouver_revocation(conn, revocation.assertion_id)
    if revocation_stockee is None:
        raise RuntimeError("La révocation locale n'a pas pu être relue après sauvegarde.")
    return revocation_stockee


def trouver_revocation(
    conn: sqlite3.Connection,
    assertion_id: str,
) -> dict[str, Any] | None:
    """Recherche une révocation par identifiant d'assertion."""

    cursor = conn.execute(
        "SELECT * FROM credential_revocations WHERE assertion_id = ?",
        (assertion_id,),
    )
    return _ligne_vers_dict(cursor.fetchone())


def est_revoque(conn: sqlite3.Connection, assertion_id: str) -> bool:
    """Indique si une assertion est révoquée dans une connexion existante."""

    revocation = trouver_revocation(conn, assertion_id)
    return bool(revocation and revocation.get("revoked"))