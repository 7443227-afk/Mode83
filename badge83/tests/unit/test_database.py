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


def test_batch_session_helpers_persist_session_and_items(tmp_path):
    db_path = tmp_path / "registry.db"
    conn = database.init_db_schema(db_path)
    try:
        session_id = database.create_batch_session(
            conn,
            {
                "id": "session-1",
                "template_id": "template-1",
                "source_filename": "participants.csv",
                "source_file_hash": "sha256$file",
                "status": "completed_with_errors",
                "total_rows": 3,
                "ready_count": 1,
                "issued_count": 1,
                "error_count": 1,
                "duplicate_count": 0,
                "not_passed_count": 1,
            },
        )
        item_id = database.add_batch_session_item(
            conn,
            {
                "session_id": session_id,
                "badge_id": "badge-1",
                "row_number": 2,
                "recipient_name": "Alice Example",
                "recipient_email": "alice@example.org",
                "recipient_email_hash": "sha256$email",
                "status": "issued",
                "error_message": "",
                "verification_url": "/verify/badge/badge-1",
            },
        )

        session = database.get_batch_session(conn, session_id)
        sessions = database.list_batch_sessions(conn)
        items = database.get_batch_session_items(conn, session_id)
    finally:
        database.close_connection(conn)

    assert session_id == "session-1"
    assert item_id == 1
    assert session is not None
    assert session["template_id"] == "template-1"
    assert session["status"] == "completed_with_errors"
    assert session["issued_count"] == 1
    assert [row["id"] for row in sessions] == ["session-1"]
    assert len(items) == 1
    assert items[0]["badge_id"] == "badge-1"
    assert items[0]["recipient_email_hash"] == "sha256$email"