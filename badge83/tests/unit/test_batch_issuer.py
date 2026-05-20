from __future__ import annotations

import json
from io import BytesIO

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


def test_parse_batch_file_normalise_les_colonnes_xlsx():
    from openpyxl import Workbook

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["Nom", "Email", "Programme", "Réussi", "Score", "Issue Date"])
    worksheet.append(["Alice Example", "ALICE@EXAMPLE.ORG", "Formation IA", "oui", 12, "2026-05-19"])
    worksheet.append([None, None, None, None, None, None])
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()

    rows = batch_issuer.parse_batch_file(buffer.getvalue(), "participants.xlsx")

    assert rows == [
        {
            "nom": "Alice Example",
            "email": "ALICE@EXAMPLE.ORG",
            "programme": "Formation IA",
            "réussi": "oui",
            "score": "12",
            "issue_date": "2026-05-19",
        }
    ]


def test_parse_batch_file_refuse_les_formats_non_supportes():
    try:
        batch_issuer.parse_batch_file(b"dummy", "participants.xls")
    except ValueError as exc:
        assert ".xls" in str(exc)
        assert ".xlsx" in str(exc)
    else:
        raise AssertionError("Le format .xls devrait être refusé")


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
    assert preview["issue_policy"] == "partial_valid_rows_only"
    assert preview["can_commit"] is True
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
    assert preview["can_commit"] is False
    assert preview["message"] == "Aucune ligne prête à émettre"
    assert preview["rows"][0]["status"] == "error"
    assert "Champ obligatoire manquant : course_name" in preview["rows"][0]["errors"]


def test_preview_batch_rows_accepte_un_champ_requis_uuid_normalise(tmp_path, monkeypatch):
    issued_dir = tmp_path / "issued"
    issued_dir.mkdir()
    monkeypatch.setattr(batch_issuer.issuer, "DATA_DIR", issued_dir)

    required_field_id = "29b19e6e-524e-4f79-9c1d-dec3aa775dbe"

    preview = batch_issuer.preview_batch_rows(
        template_id="template-1",
        rows=[
            {
                "nom": "Alice",
                "email": "alice@example.org",
                "reussi": "oui",
                "29b19e6e_524e_4f79_9c1d_dec3aa775dbe": "alice@example.org",
            }
        ],
        required_field_ids=[required_field_id],
    )

    assert preview["errors"] == 0
    assert preview["ready_rows"] == 1
    assert preview["rows"][0]["status"] == "ready"


def test_preview_batch_rows_accepte_le_label_lisible_du_champ_schema(tmp_path, monkeypatch):
    issued_dir = tmp_path / "issued"
    issued_dir.mkdir()
    monkeypatch.setattr(batch_issuer.issuer, "DATA_DIR", issued_dir)

    schema_fields = [
        {
            "id": "29b19e6e-524e-4f79-9c1d-dec3aa775dbe",
            "label": "Couriel",
            "required": True,
        }
    ]

    preview = batch_issuer.preview_batch_rows(
        template_id="template-1",
        rows=[
            {
                "nom": "Alice",
                "email": "alice@example.org",
                "reussi": "oui",
                "couriel": "alice@example.org",
            }
        ],
        schema_fields=schema_fields,
    )

    assert preview["errors"] == 0
    assert preview["ready_rows"] == 1
    assert preview["rows"][0]["status"] == "ready"
    assert preview["rows"][0]["field_values"]["29b19e6e-524e-4f79-9c1d-dec3aa775dbe"] == "alice@example.org"


def test_preview_batch_rows_reutilise_email_pour_champ_schema_couriel_requis(tmp_path, monkeypatch):
    issued_dir = tmp_path / "issued"
    issued_dir.mkdir()
    monkeypatch.setattr(batch_issuer.issuer, "DATA_DIR", issued_dir)

    schema_fields = [
        {
            "id": "29b19e6e-524e-4f79-9c1d-dec3aa775dbe",
            "label": "Couriel",
            "required": True,
        }
    ]

    preview = batch_issuer.preview_batch_rows(
        template_id="template-1",
        rows=[
            {
                "nom": "Alice",
                "email": "alice@example.org",
                "reussi": "oui",
            }
        ],
        schema_fields=schema_fields,
    )

    assert preview["errors"] == 0
    assert preview["ready_rows"] == 1
    assert preview["rows"][0]["status"] == "ready"
    assert preview["rows"][0]["field_values"]["29b19e6e-524e-4f79-9c1d-dec3aa775dbe"] == "alice@example.org"


def test_preview_batch_rows_supporte_un_volume_de_300_lignes(tmp_path, monkeypatch):
    issued_dir = tmp_path / "issued"
    issued_dir.mkdir()
    monkeypatch.setattr(batch_issuer.issuer, "DATA_DIR", issued_dir)

    rows = [
        {
            "nom": f"Participant {index}",
            "email": f"participant{index}@example.org",
            "programme": "Formation volume",
            "reussi": "oui",
        }
        for index in range(1, 301)
    ]

    preview = batch_issuer.preview_batch_rows(template_id="template-volume", rows=rows)

    assert preview["total_rows"] == 300
    assert preview["ready_rows"] == 300
    assert preview["can_commit"] is True
    assert preview["errors"] == 0
    assert preview["skipped_duplicates"] == 0
    assert preview["skipped_not_passed"] == 0
    assert preview["rows"][0]["row_number"] == 2
    assert preview["rows"][-1]["row_number"] == 301
