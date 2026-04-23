from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any

from app.config import get_registry_db_path


def _normalize_db_path(db_path: str | Path | None = None) -> Path:
    if db_path is None:
        return get_registry_db_path()
    return Path(db_path)


def _extract_admin_recipient(assertion: Dict[str, Any]) -> dict[str, Any]:
    admin_recipient = assertion.get("admin_recipient", {})
    if isinstance(admin_recipient, dict):
        return admin_recipient
    return {}


def _extract_search(assertion: Dict[str, Any]) -> dict[str, Any]:
    search = assertion.get("search", {})
    if isinstance(search, dict):
        return search
    return {}


# Database initialization
def init_database(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Initialize database connection with row factory for easy access."""
    resolved_path = _normalize_db_path(db_path)
    db_dir = os.path.dirname(str(resolved_path))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(str(resolved_path))
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection):
    """Create database tables for badge management."""
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS assertions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assertion_id TEXT UNIQUE,
                assertion_data TEXT,
                issued_on DATE,
                name TEXT,
                email TEXT,
                name_hash TEXT,
                email_hash TEXT
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_assertion_email
            ON assertions(email)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_assertion_name
            ON assertions(name)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_assertion_id
            ON assertions(assertion_id)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_assertion_email_hash
            ON assertions(email_hash)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_assertion_name_hash
            ON assertions(name_hash)
        ''')
    conn.commit()


def get_database_connection():
    """Get database connection for the registry database."""
    conn = init_database()
    return conn


def init_db_schema(db_path: str | Path | None = None):
    """Initialize the database schema."""
    conn = init_database(db_path)
    create_tables(conn)
    return conn


def build_registry_record(assertion_id: str, assertion: Dict[str, Any]) -> Dict[str, Any]:
    admin_recipient = _extract_admin_recipient(assertion)
    search = _extract_search(assertion)
    return {
        "assertion_id": assertion_id,
        "assertion_data": assertion,
        "issued_on": assertion.get("issuedOn"),
        "name": admin_recipient.get("name"),
        "email": admin_recipient.get("email"),
        "name_hash": search.get("name_hash"),
        "email_hash": search.get("email_hash"),
    }


def add_assertion(conn: sqlite3.Connection, assertion_data: Dict[str, Any]) -> int:
    """Add a new assertion to the database."""
    with conn:
        cursor = conn.execute('''
            INSERT INTO assertions (assertion_id, assertion_data, issued_on, name, email, name_hash, email_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            assertion_data.get('assertion_id'),
            json.dumps(assertion_data.get('assertion_data', {})),
            assertion_data.get('issued_on'),
            assertion_data.get('name'),
            assertion_data.get('email'),
            assertion_data.get('name_hash'),
            assertion_data.get('email_hash')
        ))
        conn.commit()
        return cursor.lastrowid


def upsert_assertion(conn: sqlite3.Connection, assertion_data: Dict[str, Any]) -> int:
    """Insert or replace an assertion registry row."""
    with conn:
        cursor = conn.execute('''
            INSERT INTO assertions (assertion_id, assertion_data, issued_on, name, email, name_hash, email_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(assertion_id) DO UPDATE SET
                assertion_data = excluded.assertion_data,
                issued_on = excluded.issued_on,
                name = excluded.name,
                email = excluded.email,
                name_hash = excluded.name_hash,
                email_hash = excluded.email_hash
        ''', (
            assertion_data.get('assertion_id'),
            json.dumps(assertion_data.get('assertion_data', {}), ensure_ascii=False),
            assertion_data.get('issued_on'),
            assertion_data.get('name'),
            assertion_data.get('email'),
            assertion_data.get('name_hash'),
            assertion_data.get('email_hash')
        ))
        conn.commit()
        return cursor.lastrowid


def get_assertion_by_id(conn: sqlite3.Connection, assertion_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an assertion by its ID."""
    cursor = conn.execute('''
        SELECT * FROM assertions WHERE assertion_id = ?
    ''', (assertion_id,))
    row = cursor.fetchone()
    if row:
        result = dict(row)
        if result.get("assertion_data"):
            try:
                result["assertion_data"] = json.loads(result["assertion_data"])
            except Exception:
                pass
        return result
    return None


def get_assertions_by_email(conn: sqlite3.Connection, email: str) -> List[Dict[str, Any]]:
    """Retrieve assertions by email."""
    cursor = conn.execute('''
        SELECT * FROM assertions WHERE email = ?
    ''', (email,))
    return [get_assertion_by_id(conn, dict(row)["assertion_id"]) for row in cursor.fetchall()]


def get_assertions_by_name(conn: sqlite3.Connection, name: str) -> List[Dict[str, Any]]:
    """Retrieve assertions by name."""
    cursor = conn.execute('''
        SELECT * FROM assertions WHERE name = ?
    ''', (name,))
    return [get_assertion_by_id(conn, dict(row)["assertion_id"]) for row in cursor.fetchall()]


def get_assertions_by_email_hash(conn: sqlite3.Connection, email_hash: str) -> List[Dict[str, Any]]:
    cursor = conn.execute('SELECT * FROM assertions WHERE email_hash = ?', (email_hash,))
    return [get_assertion_by_id(conn, dict(row)["assertion_id"]) for row in cursor.fetchall()]


def get_assertions_by_name_hash(conn: sqlite3.Connection, name_hash: str) -> List[Dict[str, Any]]:
    cursor = conn.execute('SELECT * FROM assertions WHERE name_hash = ?', (name_hash,))
    return [get_assertion_by_id(conn, dict(row)["assertion_id"]) for row in cursor.fetchall()]


def update_assertion(conn: sqlite3.Connection, assertion_id: str, assertion_data: Dict[str, Any]) -> bool:
    """Update an assertion in the database."""
    with conn:
        result = conn.execute('''
            UPDATE assertions
            SET assertion_data = ?, issued_on = ?, name = ?, email = ?, name_hash = ?, email_hash = ?
            WHERE assertion_id = ?
        ''', (
            json.dumps(assertion_data.get('assertion_data', {}), ensure_ascii=False),
            assertion_data.get('issued_on'),
            assertion_data.get('name'),
            assertion_data.get('email'),
            assertion_data.get('name_hash'),
            assertion_data.get('email_hash'),
            assertion_id
        ))
        conn.commit()
        return result.rowcount > 0


def delete_assertion(conn: sqlite3.Connection, assertion_id: str) -> bool:
    """Delete an assertion from the database."""
    with conn:
        result = conn.execute('''
            DELETE FROM assertions WHERE assertion_id = ?
        ''', (assertion_id,))
        conn.commit()
        return result.rowcount > 0


def get_all_assertions(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Retrieve all assertions."""
    cursor = conn.execute('SELECT assertion_id FROM assertions ORDER BY issued_on DESC, assertion_id DESC')
    return [get_assertion_by_id(conn, dict(row)["assertion_id"]) for row in cursor.fetchall()]


def sync_assertion_record(assertion_id: str, assertion: Dict[str, Any], db_path: str | Path | None = None) -> Dict[str, Any]:
    conn = init_db_schema(db_path)
    try:
        payload = build_registry_record(assertion_id, assertion)
        upsert_assertion(conn, payload)
        stored = get_assertion_by_id(conn, assertion_id)
        return stored or payload
    finally:
        close_connection(conn)


def delete_assertion_record(assertion_id: str, db_path: str | Path | None = None) -> bool:
    conn = init_db_schema(db_path)
    try:
        return delete_assertion(conn, assertion_id)
    finally:
        close_connection(conn)


def import_assertions_from_directory(directory: str | Path, db_path: str | Path | None = None) -> dict[str, int]:
    source_dir = Path(directory)
    source_dir.mkdir(parents=True, exist_ok=True)
    conn = init_db_schema(db_path)
    imported = 0
    skipped = 0
    try:
        for json_path in sorted(source_dir.glob("*.json")):
            try:
                assertion = json.loads(json_path.read_text(encoding="utf-8"))
            except Exception:
                skipped += 1
                continue

            assertion_id = json_path.stem
            if isinstance(assertion.get("id"), str) and assertion.get("id"):
                assertion_id = assertion["id"].rstrip("/").split("/")[-1]

            payload = build_registry_record(assertion_id, assertion)
            upsert_assertion(conn, payload)
            imported += 1
    finally:
        close_connection(conn)

    return {"imported": imported, "skipped": skipped}


def close_connection(conn: sqlite3.Connection):
    """Close database connection."""
    if conn:
        conn.close()