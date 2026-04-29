from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
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


# Initialisation de la base de données
def init_database(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Initialise la connexion à la base avec un row factory pour un accès simplifié."""
    resolved_path = _normalize_db_path(db_path)
    db_dir = os.path.dirname(str(resolved_path))
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(str(resolved_path))
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection):
    """Crée les tables de base de données pour la gestion des badges."""
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
        
        # Tables du constructeur de badges
        conn.execute('''
            CREATE TABLE IF NOT EXISTS badge_schemas (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                fields TEXT,  -- Tableau JSON de définitions de champs
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS badge_templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                schema_id TEXT,  -- Référence à badge_schemas
                background_image TEXT,  -- Chemin ou base64
                text_overlays TEXT,  -- Tableau JSON de configurations de textes superposés
                qr_code_placement TEXT DEFAULT 'bottom-right',
                qr_code_size REAL DEFAULT 0.22,
                qr_code_offset_x INTEGER DEFAULT 0,
                qr_code_offset_y INTEGER DEFAULT 0,
                qr_code_foreground_color TEXT DEFAULT '#000000',
                qr_code_background_color TEXT DEFAULT '#FFFFFF',
                qr_code_error_correction TEXT DEFAULT 'M',
                qr_code_border INTEGER DEFAULT 2,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (schema_id) REFERENCES badge_schemas(id)
            )
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_badge_schemas_name
            ON badge_schemas(name)
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_badge_templates_name
            ON badge_templates(name)
        ''')
    
    conn.commit()


def get_database_connection():
    """Retourne une connexion à la base du registre."""
    conn = init_database()
    return conn


def init_db_schema(db_path: str | Path | None = None):
    """Initialise le schéma de la base de données."""
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
    """Ajoute une nouvelle assertion dans la base de données."""
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
    """Insère ou remplace une ligne d'assertion dans le registre."""
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
    """Récupère une assertion à partir de son identifiant."""
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
    """Récupère les assertions par adresse e-mail."""
    cursor = conn.execute('''
        SELECT * FROM assertions WHERE email = ?
    ''', (email,))
    return [get_assertion_by_id(conn, dict(row)["assertion_id"]) for row in cursor.fetchall()]


def get_assertions_by_name(conn: sqlite3.Connection, name: str) -> List[Dict[str, Any]]:
    """Récupère les assertions par nom."""
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
    """Met à jour une assertion dans la base de données."""
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
    """Supprime une assertion de la base de données."""
    with conn:
        result = conn.execute('''
            DELETE FROM assertions WHERE assertion_id = ?
        ''', (assertion_id,))
        conn.commit()
        return result.rowcount > 0


def get_all_assertions(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Récupère toutes les assertions."""
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
    """Ferme la connexion à la base de données."""
    if conn:
        conn.close()


# Fonctions de base de données du constructeur de badges
def add_badge_schema(conn: sqlite3.Connection, schema_data: Dict[str, Any]) -> str:
    """Ajoute un nouveau schéma de badge à la base de données."""
    now = datetime.now(timezone.utc).isoformat()
    schema_id = schema_data.get('id')
    with conn:
        conn.execute('''
            INSERT INTO badge_schemas (id, name, description, fields, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            schema_id,
            schema_data.get('name'),
            schema_data.get('description'),
            json.dumps(schema_data.get('fields', []), ensure_ascii=False),
            schema_data.get('is_active', True),
            schema_data.get('created_at') or now,
            schema_data.get('updated_at') or now
        ))
        conn.commit()
        return schema_id


def get_badge_schema_by_id(conn: sqlite3.Connection, schema_id: str) -> Optional[Dict[str, Any]]:
    """Récupère un schéma de badge par identifiant."""
    cursor = conn.execute('''
        SELECT * FROM badge_schemas WHERE id = ?
    ''', (schema_id,))
    row = cursor.fetchone()
    if row:
        result = dict(row)
        if result.get("fields"):
            try:
                result["fields"] = json.loads(result["fields"])
            except Exception:
                pass
        return result
    return None


def get_all_badge_schemas(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Récupère tous les schémas de badge actifs."""
    cursor = conn.execute('''
        SELECT * FROM badge_schemas WHERE is_active = 1 ORDER BY name
    ''')
    schemas = []
    for row in cursor.fetchall():
        result = dict(row)
        if result.get("fields"):
            try:
                result["fields"] = json.loads(result["fields"])
            except Exception:
                pass
        schemas.append(result)
    return schemas


def update_badge_schema(conn: sqlite3.Connection, schema_data: Dict[str, Any]) -> bool:
    """Met à jour un schéma de badge existant."""
    updated_at = schema_data.get('updated_at') or datetime.now(timezone.utc).isoformat()
    with conn:
        cursor = conn.execute('''
            UPDATE badge_schemas
            SET name = ?, description = ?, fields = ?, is_active = ?, updated_at = ?
            WHERE id = ?
        ''', (
            schema_data.get('name'),
            schema_data.get('description'),
            json.dumps(schema_data.get('fields', []), ensure_ascii=False),
            schema_data.get('is_active', True),
            updated_at,
            schema_data.get('id')
        ))
        conn.commit()
        return cursor.rowcount > 0


def delete_badge_schema(conn: sqlite3.Connection, schema_id: str) -> bool:
    """Supprime logiquement un schéma de badge en désactivant is_active."""
    with conn:
        cursor = conn.execute('''
            UPDATE badge_schemas
            SET is_active = 0, updated_at = ?
            WHERE id = ?
        ''', (
            datetime.now(timezone.utc).isoformat(),
            schema_id
        ))
        conn.commit()
        return cursor.rowcount > 0


def add_badge_template(conn: sqlite3.Connection, template_data: Dict[str, Any]) -> str:
    """Ajoute un nouveau modèle de badge à la base de données."""
    now = datetime.now(timezone.utc).isoformat()
    template_id = template_data.get('id')
    with conn:
        conn.execute('''
            INSERT INTO badge_templates (
                id, name, description, schema_id, background_image, text_overlays,
                qr_code_placement, qr_code_size, qr_code_offset_x, qr_code_offset_y,
                qr_code_foreground_color, qr_code_background_color,
                qr_code_error_correction, qr_code_border, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            template_id,
            template_data.get('name'),
            template_data.get('description'),
            template_data.get('schema_id'),
            template_data.get('background_image'),
            json.dumps(template_data.get('text_overlays', []), ensure_ascii=False),
            template_data.get('qr_code_placement', 'bottom-right'),
            template_data.get('qr_code_size', 0.22),
            template_data.get('qr_code_offset_x', 0),
            template_data.get('qr_code_offset_y', 0),
            template_data.get('qr_code_foreground_color', '#000000'),
            template_data.get('qr_code_background_color', '#FFFFFF'),
            template_data.get('qr_code_error_correction', 'M'),
            template_data.get('qr_code_border', 2),
            template_data.get('is_active', True),
            template_data.get('created_at') or now,
            template_data.get('updated_at') or now
        ))
        conn.commit()
        return template_id


def get_badge_template_by_id(conn: sqlite3.Connection, template_id: str) -> Optional[Dict[str, Any]]:
    """Récupère un modèle de badge par identifiant."""
    cursor = conn.execute('''
        SELECT * FROM badge_templates WHERE id = ?
    ''', (template_id,))
    row = cursor.fetchone()
    if row:
        result = dict(row)
        if result.get("text_overlays"):
            try:
                result["text_overlays"] = json.loads(result["text_overlays"])
            except Exception:
                pass
        return result
    return None


def get_all_badge_templates(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Récupère tous les modèles de badge actifs."""
    cursor = conn.execute('''
        SELECT bt.*, bs.name as schema_name 
        FROM badge_templates bt
        LEFT JOIN badge_schemas bs ON bt.schema_id = bs.id
        WHERE bt.is_active = 1
        ORDER BY bt.name
    ''')
    templates = []
    for row in cursor.fetchall():
        result = dict(row)
        if result.get("text_overlays"):
            try:
                result["text_overlays"] = json.loads(result["text_overlays"])
            except Exception:
                pass
        templates.append(result)
    return templates


def update_badge_template(conn: sqlite3.Connection, template_data: Dict[str, Any]) -> bool:
    """Met à jour un modèle de badge existant."""
    updated_at = template_data.get('updated_at') or datetime.now(timezone.utc).isoformat()
    with conn:
        cursor = conn.execute('''
            UPDATE badge_templates
            SET name = ?, description = ?, schema_id = ?, background_image = ?, text_overlays = ?,
                qr_code_placement = ?, qr_code_size = ?, qr_code_offset_x = ?, qr_code_offset_y = ?,
                qr_code_foreground_color = ?, qr_code_background_color = ?,
                qr_code_error_correction = ?, qr_code_border = ?, updated_at = ?
            WHERE id = ?
        ''', (
            template_data.get('name'),
            template_data.get('description'),
            template_data.get('schema_id'),
            template_data.get('background_image'),
            json.dumps(template_data.get('text_overlays', []), ensure_ascii=False),
            template_data.get('qr_code_placement', 'bottom-right'),
            template_data.get('qr_code_size', 0.22),
            template_data.get('qr_code_offset_x', 0),
            template_data.get('qr_code_offset_y', 0),
            template_data.get('qr_code_foreground_color', '#000000'),
            template_data.get('qr_code_background_color', '#FFFFFF'),
            template_data.get('qr_code_error_correction', 'M'),
            template_data.get('qr_code_border', 2),
            updated_at,
            template_data.get('id')
        ))
        conn.commit()
        return cursor.rowcount > 0


def delete_badge_template(conn: sqlite3.Connection, template_id: str) -> bool:
    """Supprime logiquement un modèle de badge en désactivant is_active."""
    with conn:
        cursor = conn.execute('''
            UPDATE badge_templates
            SET is_active = 0, updated_at = ?
            WHERE id = ?
        ''', (
            datetime.now(timezone.utc).isoformat(),
            template_id
        ))
        conn.commit()
        return cursor.rowcount > 0