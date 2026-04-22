from __future__ import annotations

import json

from app import issuer


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
    assert assertion["id"] == f"https://tests.mode83.local/assertions/{assertion_id}"
    assert assertion["verification"]["type"] == "HostedBadge"
    assert assertion["recipient"]["hashed"] is True
    assert assertion["admin_recipient"] == {
        "name": "Alice Example",
        "email": "alice@example.com",
    }

    persisted = json.loads(saved_path.read_text(encoding="utf-8"))
    assert persisted == assertion
    assert result["issuer"]["id"] == "https://tests.mode83.local/issuers/main"
    assert result["badgeclass"]["id"] == "https://tests.mode83.local/badges/blockchain-foundations"


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