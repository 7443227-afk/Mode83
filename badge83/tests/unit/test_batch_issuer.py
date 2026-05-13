from __future__ import annotations

import json

from app import batch_issuer


def test_parse_batch_file_normalise_les_colonnes_csv():
    content = "Nom;Email;Programme;Réussi\nAlice Example;ALICE@EXAMPLE.ORG;Formation IA;oui\n".encode("utf-8")

    rows = batch_issuer.parse_batch_file(content, "participants.csv")

    assert rows == [
        {
            "nom": "Alice Example",
            "email": "ALICE@EXAMPLE.ORG",
            "programme": "Formation IA",
            "réussi": "oui",
        }
    ]


def test_is_passed_reconnait_les_valeurs_attendues():
    assert batch_issuer.is_passed("oui") is True
    assert batch_issuer.is_passed("validé") is True
    assert batch_issuer.is_passed("no") is False
    assert batch_issuer.is_passed("absent") is False
    assert batch_issuer.is_passed("à vérifier") is None


def test_preview_batch_rows_classe_ready_not_passed_error_et_duplicate(tmp_path, monkeypatch):
    issued_dir = tmp_path / "issued"
    issued_dir.mkdir()
    existing_assertion = {
        "badge83_template": {"id": "template-1"},
        "admin_recipient": {"email": "deja@example.org"},
    }
    (issued_dir / "existing.json").write_text(json.dumps(existing_assertion), encoding="utf-8")
    monkeypatch.setattr(batch_issuer.issuer, "DATA_DIR", issued_dir)

    rows = [
        {"nom": "Alice", "email": "alice@example.org", "programme": "Formation IA", "reussi": "oui"},
        {"nom": "Bob", "email": "bob@example.org", "programme": "Formation IA", "reussi": "non"},
        {"nom": "Invalid", "email": "invalid", "programme": "Formation IA", "reussi": "oui"},
        {"nom": "Déjà", "email": "deja@example.org", "programme": "Formation IA", "reussi": "oui"},
        {"nom": "Alice Bis", "email": "alice@example.org", "programme": "Formation IA", "reussi": "oui"},
    ]

    preview = batch_issuer.preview_batch_rows(template_id="template-1", rows=rows)

    assert preview["total_rows"] == 5
    assert preview["ready_rows"] == 1
    assert preview["skipped_not_passed"] == 1
    assert preview["errors"] == 1
    assert preview["skipped_duplicates"] == 2
    assert [row["status"] for row in preview["rows"]] == [
        "ready",
        "not_passed",
        "error",
        "duplicate",
        "duplicate",
    ]


def test_preview_batch_rows_signale_un_champ_requis_manquant(tmp_path, monkeypatch):
    issued_dir = tmp_path / "issued"
    issued_dir.mkdir()
    monkeypatch.setattr(batch_issuer.issuer, "DATA_DIR", issued_dir)

    preview = batch_issuer.preview_batch_rows(
        template_id="template-1",
        rows=[{"nom": "Alice", "email": "alice@example.org", "reussi": "oui"}],
        required_field_ids=["course_name"],
    )

    assert preview["errors"] == 1
    assert preview["rows"][0]["status"] == "error"
    assert "Champ obligatoire manquant : course_name" in preview["rows"][0]["errors"]
