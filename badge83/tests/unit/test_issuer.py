from __future__ import annotations

import json

from app import issuer
from app.baker import unbake_badge


def test_normalize_email_and_name():
    assert issuer.normalize_email("  USER@Example.COM ") == "user@example.com"
    assert issuer.normalize_name("  Alice   Dupond  ") == "alice dupond"


def test_make_search_metadata_uses_normalized_values(monkeypatch):
    monkeypatch.setenv("BADGE83_SEARCH_PEPPER", "pepper-123")

    metadata = issuer.make_search_metadata("  Alice   Dupond  ", " USER@Example.COM ")

    assert metadata["name_hash"] == issuer.make_search_hash("alice dupond")
    assert metadata["email_hash"] == issuer.make_search_hash("user@example.com")


def test_issue_badge_persists_assertion_and_metadata(isolated_issuer_env):
    result = issuer.issue_badge(name="Alice Example", email="Alice@example.com")

    assertion_id = result["assertion_id"]
    assertion = result["assertion"]
    saved_path = isolated_issuer_env["issued_dir"] / f"{assertion_id}.json"

    assert saved_path.exists()
    assert assertion["type"] == "Assertion"
    assert assertion["@language"] == "fr-FR"
    assert assertion["id"] == f"https://tests.mode83.local/assertions/{assertion_id}"
    assert assertion["verification"]["type"] == "HostedBadge"
    assert assertion["expires"]
    assert assertion["evidence"][0]["type"] == "Evidence"
    assert assertion["evidence"][0]["id"] == f"https://tests.mode83.local/evidence/{assertion_id}"
    assert assertion["recipient"]["hashed"] is True
    assert assertion["admin_recipient"] == {
        "name": "Alice Example",
        "email": "alice@example.com",
    }

    persisted = json.loads(saved_path.read_text(encoding="utf-8"))
    assert persisted == assertion
    assert result["issuer"]["id"] == "https://tests.mode83.local/issuers/main"
    assert result["issuer"]["@language"] == "fr-FR"
    assert result["issuer"]["verification"]["type"] == "VerificationObject"
    assert result["issuer"]["verification"]["allowedOrigins"] == ["tests.mode83.local"]
    assert result["issuer"]["verification"]["startsWith"] == ["https://tests.mode83.local/assertions/"]
    assert result["badgeclass"]["id"] == "https://tests.mode83.local/badges/blockchain-foundations"
    assert result["badgeclass"]["@language"] == "fr-FR"
    assert "mode83" in result["badgeclass"]["tags"]
    assert result["badgeclass"]["alignment"][0]["type"] == "AlignmentObject"


def test_issue_baked_badge_creates_png_and_qr_url(isolated_issuer_env, sample_png_bytes):
    result = issuer.issue_baked_badge(
        name="Alice Example",
        email="alice@example.com",
        png_data=sample_png_bytes,
    )

    baked_path = isolated_issuer_env["baked_dir"] / f"{result['assertion_id']}.png"

    assert baked_path.exists()
    assert result["baked_png_bytes"].startswith(b"\x89PNG\r\n\x1a\n")
    assert result["baked_png_path"] == str(baked_path)
    assert result["baked_download_filename"].endswith(".png")
    assert result["verification_page_url"] == (
        f"https://tests.mode83.local/verify/qr/{result['assertion_id']}"
    )


def test_issue_baked_badge_from_template_persists_field_values(isolated_issuer_env, sample_png_bytes):
    template = {
        "id": "template-1",
        "name": "Blockchain Foundations Standard",
        "schema_id": "schema-1",
        "text_overlays": [
            {
                "content_type": "field",
                "field_id": "course_name",
                "position_x": 16,
                "position_y": 16,
                "font_size": 18,
                "font_color": "#000000",
            },
            {
                "content_type": "field",
                "field_id": "certificate_number",
                "position_x": 16,
                "position_y": 48,
                "font_size": 14,
                "font_color": "#000000",
            },
            {
                "content_type": "field",
                "field_id": "name",
                "position_x": 16,
                "position_y": 80,
                "font_size": 14,
                "font_color": "#000000",
            },
        ],
        "qr_code_placement": "bottom-right",
        "qr_code_size": 0.2,
    }
    field_values = {
        "course_name": "Blockchain Foundations",
        "certificate_number": "BF-2026-001",
    }

    result = issuer.issue_baked_badge_from_template(
        name="Alice Example",
        email="alice@example.com",
        template=template,
        field_values=field_values,
        png_data=sample_png_bytes,
    )

    assertion_id = result["assertion_id"]
    baked_path = isolated_issuer_env["baked_dir"] / f"{assertion_id}.png"
    saved_path = isolated_issuer_env["issued_dir"] / f"{assertion_id}.json"
    extracted = unbake_badge(result["baked_png_bytes"])

    assert baked_path.exists()
    assert saved_path.exists()
    assert extracted["id"] == f"https://tests.mode83.local/assertions/{assertion_id}"
    assert extracted["field_values"] == field_values
    assert extracted["badge83_template"] == {
        "id": "template-1",
        "name": "Blockchain Foundations Standard",
        "schema_id": "schema-1",
    }
    assert extracted["admin_recipient"] == {
        "name": "Alice Example",
        "email": "alice@example.com",
    }
    assert json.loads(saved_path.read_text(encoding="utf-8")) == extracted