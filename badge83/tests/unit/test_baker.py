from __future__ import annotations

import json
import struct
import zlib

import pytest

from app.baker import bake_badge_from_bytes, unbake_badge
from app.verifier import deep_verify_baked_badge


def _count_openbadges_chunks(png_data: bytes) -> int:
    count = 0
    pos = 8
    while pos + 8 <= len(png_data):
        length = struct.unpack(">I", png_data[pos:pos + 4])[0]
        chunk_type = png_data[pos + 4:pos + 8]
        data = png_data[pos + 8:pos + 8 + length]
        if chunk_type in (b"tEXt", b"iTXt") and data.startswith(b"openbadges\x00"):
            count += 1
        pos += 4 + 4 + length + 4
    return count


def _make_itxt_chunk(keyword: str, text: str) -> bytes:
    payload = (
        keyword.encode("latin-1")
        + b"\x00"
        + b"\x00"
        + b"\x00"
        + b"\x00"
        + b"\x00"
        + text.encode("utf-8")
    )
    chunk_type = b"iTXt"
    crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def _insert_before_iend(png_data: bytes, chunk: bytes) -> bytes:
    idx = png_data.rfind(b"IEND")
    return png_data[:idx - 4] + chunk + png_data[idx - 4:]


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
    assert _count_openbadges_chunks(baked_twice) == 1


def test_unbake_reads_legacy_itxt_openbadges_chunk(sample_png_bytes):
    assertion = {"id": "itxt", "type": "Assertion", "badge": "badge", "issuer": "issuer"}
    chunk = _make_itxt_chunk("openbadges", json.dumps(assertion, separators=(",", ":")))
    baked = _insert_before_iend(sample_png_bytes, chunk)

    assert unbake_badge(baked) == assertion


def test_unbake_rejects_png_without_openbadges_chunk(sample_png_bytes):
    with pytest.raises(ValueError, match="Aucune assertion Open Badges"):
        unbake_badge(sample_png_bytes)


def test_unbake_rejects_non_png_bytes():
    with pytest.raises(ValueError, match="signature incorrecte"):
        unbake_badge(b"not-a-png")


def test_deep_verify_baked_badge_resolves_hosted_chain(sample_png_bytes):
    assertion = {
        "id": "https://tests.mode83.local/assertions/123",
        "type": "Assertion",
        "badge": "https://tests.mode83.local/badges/blockchain-foundations",
        "issuer": "https://tests.mode83.local/issuers/main",
        "issuedOn": "2026-04-22T12:00:00+00:00",
        "recipient": {
            "type": "email",
            "hashed": True,
            "salt": "abc",
            "identity": "sha256$123",
        },
        "verification": {
            "type": "HostedBadge",
            "url": "https://tests.mode83.local/assertions/123",
        },
    }
    badgeclass = {
        "id": "https://tests.mode83.local/badges/blockchain-foundations",
        "type": "BadgeClass",
        "issuer": "https://tests.mode83.local/issuers/main",
    }
    issuer = {"id": "https://tests.mode83.local/issuers/main", "type": "Issuer", "name": "Mode83"}
    documents = {
        assertion["id"]: assertion,
        assertion["badge"]: badgeclass,
        assertion["issuer"]: issuer,
    }

    baked = bake_badge_from_bytes(sample_png_bytes, assertion)
    result = deep_verify_baked_badge(baked, fetch_json=documents.__getitem__)

    assert result["valid"] is True
    assert result["deep"]["ok"] is True
    assert result["deep"]["comparison"]["matches"] is True
    assert result["deep"]["badgeclass"]["document"] == badgeclass
    assert result["deep"]["issuer"]["document"] == issuer