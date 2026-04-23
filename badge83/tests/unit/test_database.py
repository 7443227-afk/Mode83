from __future__ import annotations

import json

from app import database


def test_sync_assertion_record_persists_searchable_fields(tmp_path, monkeypatch):
    db_path = tmp_path / "registry.db"
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(db_path))

    assertion_id = "abc-123"
    assertion = {
        "id": "https://tests.mode83.local/assertions/abc-123",
        "type": "Assertion",
        "issuedOn": "2026-04-23T09:00:00+00:00",
        "admin_recipient": {
            "name": "Alice Example",
            "email": "alice@example.com",
        },
        "search": {
            "name_hash": "sha256$name",
            "email_hash": "sha256$email",
        },
    }

    stored = database.sync_assertion_record(assertion_id, assertion, db_path)

    assert stored is not None
    assert stored["assertion_id"] == assertion_id
    assert stored["name"] == "Alice Example"
    assert stored["email"] == "alice@example.com"
    assert stored["assertion_data"]["id"].endswith(assertion_id)


def test_import_assertions_from_directory_imports_existing_json(tmp_path):
    issued_dir = tmp_path / "issued"
    issued_dir.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "registry.db"

    source = {
        "id": "https://tests.mode83.local/assertions/import-1",
        "type": "Assertion",
        "issuedOn": "2026-04-23T09:00:00+00:00",
        "admin_recipient": {"name": "Bob Example", "email": "bob@example.com"},
        "search": {"name_hash": "sha256$n", "email_hash": "sha256$e"},
    }
    (issued_dir / "import-1.json").write_text(json.dumps(source), encoding="utf-8")

    stats = database.import_assertions_from_directory(issued_dir, db_path)
    conn = database.init_db_schema(db_path)
    try:
        row = database.get_assertion_by_id(conn, "import-1")
    finally:
        database.close_connection(conn)

    assert stats == {"imported": 1, "skipped": 0}
    assert row is not None
    assert row["name"] == "Bob Example"
    assert row["email_hash"] == "sha256$e"