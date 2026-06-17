from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app import database


def _maintenant_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ligne_vers_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


class BlockchainRevocationRepository:
    """Persistance SQLite des publications de révocation blockchain optionnelles."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = db_path

    def initialiser_connexion(self) -> sqlite3.Connection:
        return database.init_db_schema(self.db_path)

    def enregistrer(
        self,
        *,
        assertion_id: str,
        credential_hash: str,
        provider: str,
        status: str,
        network: str | None = None,
        tx_hash: str | None = None,
        block_number: int | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        conn = self.initialiser_connexion()
        try:
            return enregistrer_revocation_blockchain(
                conn,
                assertion_id=assertion_id,
                credential_hash=credential_hash,
                provider=provider,
                network=network,
                status=status,
                tx_hash=tx_hash,
                block_number=block_number,
                error_message=error_message,
            )
        finally:
            database.close_connection(conn)

    def lister_par_assertion(self, assertion_id: str) -> list[dict[str, Any]]:
        conn = self.initialiser_connexion()
        try:
            return lister_revocations_blockchain_par_assertion(conn, assertion_id)
        finally:
            database.close_connection(conn)

    def derniere_par_assertion(self, assertion_id: str) -> dict[str, Any] | None:
        items = self.lister_par_assertion(assertion_id)
        return items[-1] if items else None


def enregistrer_revocation_blockchain(
    conn: sqlite3.Connection,
    *,
    assertion_id: str,
    credential_hash: str,
    provider: str,
    status: str,
    network: str | None = None,
    tx_hash: str | None = None,
    block_number: int | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    now = _maintenant_iso()
    with conn:
        cursor = conn.execute(
            '''
            INSERT INTO blockchain_revocations (
                assertion_id, credential_hash, provider, network, status, tx_hash,
                block_number, error_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                assertion_id,
                credential_hash,
                provider,
                network,
                status,
                tx_hash,
                block_number,
                error_message,
                now,
                now,
            ),
        )
        conn.commit()

    revocation = trouver_revocation_blockchain(conn, cursor.lastrowid)
    if revocation is None:
        raise RuntimeError("La révocation blockchain n'a pas pu être relue après sauvegarde.")
    return revocation


def trouver_revocation_blockchain(conn: sqlite3.Connection, revocation_id: int) -> dict[str, Any] | None:
    cursor = conn.execute("SELECT * FROM blockchain_revocations WHERE id = ?", (revocation_id,))
    return _ligne_vers_dict(cursor.fetchone())


def lister_revocations_blockchain_par_assertion(
    conn: sqlite3.Connection,
    assertion_id: str,
) -> list[dict[str, Any]]:
    cursor = conn.execute(
        "SELECT * FROM blockchain_revocations WHERE assertion_id = ? ORDER BY id ASC",
        (assertion_id,),
    )
    return [_ligne_vers_dict(row) for row in cursor.fetchall() if row is not None]