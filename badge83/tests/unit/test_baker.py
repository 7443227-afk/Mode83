from __future__ import annotations

import json

import pytest

from app.baker import bake_badge_from_bytes, unbake_badge


def test_bake_and_unbake_roundtrip(sample_png_bytes):
    assertion = {
        "id": "https://tests.mode83.local/assertions/123",
        "type": "Assertion",
        "badge": "https://tests.mode83.local/badges/blockchain-foundations",
        "issuer": "https://tests.mode83.local/issuers/main",
        "issuedOn": "2026-04-22T12:00:00+00:00",
    }

    baked = bake_badge_from_bytes(sample_png_bytes, assertion)
    extracted = unbake_badge(baked)

    assert baked.startswith(b"\x89PNG\r\n\x1a\n")
    assert extracted == assertion


def test_rebaking_replaces_existing_openbadges_chunk(sample_png_bytes):
    first_assertion = {"id": "first", "type": "Assertion"}
    second_assertion = {"id": "second", "type": "Assertion"}

    baked_once = bake_badge_from_bytes(sample_png_bytes, first_assertion)
    baked_twice = bake_badge_from_bytes(baked_once, second_assertion)
    extracted = unbake_badge(baked_twice)

    assert extracted == second_assertion
    assert json.dumps(first_assertion, ensure_ascii=False).encode("utf-8") not in baked_twice


def test_unbake_rejects_non_png_bytes():
    with pytest.raises(ValueError, match="signature incorrecte"):
        unbake_badge(b"not-a-png")