from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app import database
from app.proofs.audit import AuditEvent


def _ligne_vers_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    result = dict(row)
    payload = result.get("payload")
    if payload:
        try:
            result["payload"] = json.loads(payload)
        except json.JSONDecodeError:
            result["payload"] = {}
    else:
        result["payload"] = {}
    return result


class AuditRepository:
    """Persistance SQLite des événements d'audit Badge83."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = db_path

    def initialiser_connexion(self) -> sqlite3.Connection:
        return database.init_db_schema(self.db_path)

    def enregistrer(self, evenement: AuditEvent) -> dict[str, Any]:
        conn = self.initialiser_connexion()
        try:
            return enregistrer_evenement(conn, evenement)
        finally:
            database.close_connection(conn)

    def lister_par_assertion(self, assertion_id: str) -> list[dict[str, Any]]:
        conn = self.initialiser_connexion()
        try:
            return lister_evenements_par_assertion(conn, assertion_id)
        finally:
            database.close_connection(conn)


def enregistrer_evenement(conn: sqlite3.Connection, evenement: AuditEvent) -> dict[str, Any]:
    payload_json = json.dumps(evenement.payload, ensure_ascii=False, sort_keys=True)
    with conn:
        conn.execute(
            '''
            INSERT INTO audit_events (
                event_id, event_type, actor, assertion_id, credential_hash, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                evenement.event_id,
                evenement.event_type,
                evenement.actor,
                evenement.assertion_id,
                evenement.credential_hash,
                payload_json,
                evenement.created_at,
            ),
        )
        conn.commit()

    cursor = conn.execute("SELECT * FROM audit_events WHERE event_id = ?", (evenement.event_id,))
    evenement_stocke = _ligne_vers_dict(cursor.fetchone())
    if evenement_stocke is None:
        raise RuntimeError("L'événement d'audit n'a pas pu être relu après sauvegarde.")
    return evenement_stocke


def lister_evenements_par_assertion(conn: sqlite3.Connection, assertion_id: str) -> list[dict[str, Any]]:
    cursor = conn.execute(
        "SELECT * FROM audit_events WHERE assertion_id = ? ORDER BY id ASC",
        (assertion_id,),
    )
    return [_ligne_vers_dict(row) for row in cursor.fetchall() if row is not None]