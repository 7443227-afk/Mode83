from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app import issuer


RESERVED_COLUMNS = {
    "name",
    "nom",
    "email",
    "programme",
    "program",
    "reussi",
    "réussi",
    "passed",
}

POSITIVE_VALUES = {"oui", "yes", "true", "1", "reussi", "réussi", "passed", "valide", "validé"}
NEGATIVE_VALUES = {"non", "no", "false", "0", "echoue", "échoué", "failed", "absent"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class BatchRow:
    row_number: int
    status: str
    name: str | None
    email: str | None
    field_values: dict[str, str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_number": self.row_number,
            "status": self.status,
            "name": self.name,
            "email": self.email,
            "field_values": self.field_values,
            "errors": self.errors,
        }


def normalize_column_name(value: str) -> str:
    """Normalise un nom de colonne CSV pour accepter quelques variantes opérateur."""
    normalized = unicodedata.normalize("NFKC", str(value or "")).strip().lower()
    normalized = normalized.replace(" ", "_").replace("-", "_")
    normalized = re.sub(r"_+", "_", normalized)
    return normalized


def normalize_email_value(value: object) -> str:
    return str(value or "").strip().lower()


def is_passed(value: object) -> bool | None:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None
    if normalized in POSITIVE_VALUES:
        return True
    if normalized in NEGATIVE_VALUES:
        return False
    return None


def parse_batch_file(file_bytes: bytes, filename: str) -> list[dict[str, str]]:
    """Parse un fichier CSV d'émission groupée.

    Le MVP supporte uniquement CSV. Le support XLSX est prévu dans une phase suivante.
    """
    suffix = Path(filename or "").suffix.lower()
    if suffix != ".csv":
        raise ValueError("Seuls les fichiers CSV sont supportés dans cette première version")

    text = file_bytes.decode("utf-8-sig")
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise ValueError("Le fichier CSV doit contenir une ligne d'en-tête")

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        normalized_row: dict[str, str] = {}
        for key, value in raw_row.items():
            normalized_key = normalize_column_name(key or "")
            if normalized_key:
                normalized_row[normalized_key] = str(value or "").strip()
        if any(value for value in normalized_row.values()):
            rows.append(normalized_row)
    return rows


def _get_first(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _build_field_values(row: dict[str, str]) -> dict[str, str]:
    field_values = {
        key: str(value).strip()
        for key, value in row.items()
        if key not in RESERVED_COLUMNS and str(value).strip()
    }
    programme = _get_first(row, "programme", "program")
    if programme:
        field_values.setdefault("programme", programme)
        field_values.setdefault("course_name", programme)
    return field_values


def _iter_existing_template_emails(template_id: str) -> set[str]:
    existing: set[str] = set()
    issued_dir = issuer.DATA_DIR
    if not issued_dir.exists():
        return existing

    for assertion_path in issued_dir.glob("*.json"):
        try:
            assertion = json.loads(assertion_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        template_meta = assertion.get("badge83_template") if isinstance(assertion.get("badge83_template"), dict) else {}
        if template_meta.get("id") != template_id:
            continue
        admin_recipient = assertion.get("admin_recipient") if isinstance(assertion.get("admin_recipient"), dict) else {}
        email = normalize_email_value(admin_recipient.get("email"))
        if email:
            existing.add(email)
    return existing


def preview_batch_rows(
    *,
    template_id: str,
    rows: list[dict[str, str]],
    required_field_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Classe les lignes CSV sans émettre de badge."""
    required_field_ids = required_field_ids or []
    existing_emails = _iter_existing_template_emails(template_id)
    seen_emails: set[str] = set()
    prepared_rows: list[BatchRow] = []

    for index, row in enumerate(rows, start=2):
        errors: list[str] = []
        name = _get_first(row, "nom", "name")
        email = normalize_email_value(_get_first(row, "email"))
        passed_raw = _get_first(row, "reussi", "réussi", "passed")
        passed = is_passed(passed_raw)
        field_values = _build_field_values(row)

        if not name:
            errors.append("Nom manquant")
        if not email or not EMAIL_RE.match(email):
            errors.append("Email invalide")
        if passed is None:
            errors.append("Statut de réussite ambigu ou manquant")

        for field_id in required_field_ids:
            if field_id in {"name", "nom", "email"}:
                continue
            if not str(field_values.get(field_id, "")).strip():
                errors.append(f"Champ obligatoire manquant : {field_id}")

        if errors:
            status = "error"
        elif passed is False:
            status = "not_passed"
        elif email in existing_emails or email in seen_emails:
            status = "duplicate"
        else:
            status = "ready"

        if email:
            seen_emails.add(email)

        prepared_rows.append(
            BatchRow(
                row_number=index,
                status=status,
                name=name or None,
                email=email or None,
                field_values=field_values,
                errors=errors,
            )
        )

    return build_batch_summary(template_id=template_id, rows=prepared_rows)


def preview_batch_file(
    *,
    template_id: str,
    file_bytes: bytes,
    filename: str,
    required_field_ids: list[str] | None = None,
) -> dict[str, Any]:
    rows = parse_batch_file(file_bytes, filename)
    return preview_batch_rows(template_id=template_id, rows=rows, required_field_ids=required_field_ids)


def build_batch_summary(*, template_id: str, rows: list[BatchRow]) -> dict[str, Any]:
    counters = {
        "ready": 0,
        "not_passed": 0,
        "duplicate": 0,
        "error": 0,
    }
    for row in rows:
        counters[row.status] = counters.get(row.status, 0) + 1

    return {
        "template_id": template_id,
        "total_rows": len(rows),
        "ready_rows": counters["ready"],
        "skipped_not_passed": counters["not_passed"],
        "skipped_duplicates": counters["duplicate"],
        "errors": counters["error"],
        "rows": [row.to_dict() for row in rows],
    }
