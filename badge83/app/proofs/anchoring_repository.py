from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app import database
from app.proofs.anchoring import AnchoringTransaction, normaliser_statut_ancrage


def _maintenant_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ligne_vers_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


class AnchoringRepository:
    """Persistance SQLite de la file d'attente d'ancrage locale."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = db_path

    def initialiser_connexion(self) -> sqlite3.Connection:
        return database.init_db_schema(self.db_path)

    def enqueue(
        self,
        assertion_id: str,
        credential_hash: str,
        provider: str = "noop",
        network: str | None = None,
    ) -> dict[str, Any]:
        conn = self.initialiser_connexion()
        try:
            return enregistrer_transaction(
                conn,
                AnchoringTransaction(
                    assertion_id=assertion_id,
                    credential_hash=credential_hash,
                    provider=provider,
                    network=network,
                    status="queued",
                ),
            )
        finally:
            database.close_connection(conn)

    def changer_statut(
        self,
        transaction_id: int,
        status: str,
        *,
        tx_hash: str | None = None,
        block_number: int | None = None,
        error_message: str | None = None,
        next_retry_at: str | None = None,
        increment_attempts: bool = False,
    ) -> dict[str, Any]:
        conn = self.initialiser_connexion()
        try:
            return changer_statut_transaction(
                conn,
                transaction_id,
                status,
                tx_hash=tx_hash,
                block_number=block_number,
                error_message=error_message,
                next_retry_at=next_retry_at,
                increment_attempts=increment_attempts,
            )
        finally:
            database.close_connection(conn)

    def lister_par_statut(self, status: str) -> list[dict[str, Any]]:
        conn = self.initialiser_connexion()
        try:
            return lister_transactions_par_statut(conn, status)
        finally:
            database.close_connection(conn)

    def trouver(self, transaction_id: int) -> dict[str, Any] | None:
        conn = self.initialiser_connexion()
        try:
            return trouver_transaction(conn, transaction_id)
        finally:
            database.close_connection(conn)


def enregistrer_transaction(conn: sqlite3.Connection, transaction: AnchoringTransaction) -> dict[str, Any]:
    with conn:
        cursor = conn.execute(
            '''
            INSERT INTO anchoring_transactions (
                assertion_id, credential_hash, provider, network, status, tx_hash,
                block_number, error_message, attempts, next_retry_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                transaction.assertion_id,
                transaction.credential_hash,
                transaction.provider,
                transaction.network,
                transaction.status,
                transaction.tx_hash,
                transaction.block_number,
                transaction.error_message,
                transaction.attempts,
                transaction.next_retry_at,
                transaction.created_at,
                transaction.updated_at,
            ),
        )
        conn.commit()

    transaction_stockee = trouver_transaction(conn, cursor.lastrowid)
    if transaction_stockee is None:
        raise RuntimeError("La transaction d'ancrage n'a pas pu être relue après sauvegarde.")
    return transaction_stockee


def trouver_transaction(conn: sqlite3.Connection, transaction_id: int) -> dict[str, Any] | None:
    cursor = conn.execute("SELECT * FROM anchoring_transactions WHERE id = ?", (transaction_id,))
    return _ligne_vers_dict(cursor.fetchone())


def changer_statut_transaction(
    conn: sqlite3.Connection,
    transaction_id: int,
    status: str,
    *,
    tx_hash: str | None = None,
    block_number: int | None = None,
    error_message: str | None = None,
    next_retry_at: str | None = None,
    increment_attempts: bool = False,
) -> dict[str, Any]:
    statut = normaliser_statut_ancrage(status)
    with conn:
        conn.execute(
            '''
            UPDATE anchoring_transactions
            SET status = ?,
                tx_hash = COALESCE(?, tx_hash),
                block_number = COALESCE(?, block_number),
                error_message = ?,
                next_retry_at = ?,
                attempts = attempts + ?,
                updated_at = ?
            WHERE id = ?
            ''',
            (
                statut,
                tx_hash,
                block_number,
                error_message,
                next_retry_at,
                1 if increment_attempts else 0,
                _maintenant_iso(),
                transaction_id,
            ),
        )
        conn.commit()

    transaction = trouver_transaction(conn, transaction_id)
    if transaction is None:
        raise RuntimeError("Transaction d'ancrage introuvable après mise à jour.")
    return transaction


def lister_transactions_par_statut(conn: sqlite3.Connection, status: str) -> list[dict[str, Any]]:
    cursor = conn.execute(
        "SELECT * FROM anchoring_transactions WHERE status = ? ORDER BY id ASC",
        (normaliser_statut_ancrage(status),),
    )
    return [_ligne_vers_dict(row) for row in cursor.fetchall() if row is not None]