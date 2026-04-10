"""
Open Badges PNG Baking / Unbaking utilities.

Baking  = embedding assertion JSON into a PNG as a ``tEXt`` chunk
          with the keyword ``openbadges`` (per Open Badges specification).

Unbaking = extracting that JSON back out of a baked PNG.
"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path
from typing import Any

# PNG signature: 8 bytes
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# Keyword used in the PNG tEXt chunk per Open Badges spec
OB_KEYWORD = "openbadges"


# ---------------------------------------------------------------------------
# Baking — embed JSON into a PNG
# ---------------------------------------------------------------------------

def _make_text_chunk(keyword: str, text: str) -> bytes:
    """Build a PNG ``tEXt`` chunk.

    Format:  length (4B) | type (4B) | keyword | NUL | text | CRC (4B)
    """
    payload = keyword.encode("latin-1") + b"\x00" + text.encode("utf-8")
    chunk_type = b"tEXt"
    crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def _insert_chunk_before_iend(png_data: bytes, chunk: bytes) -> bytes:
    """Insert *chunk* just before the ``IEND`` chunk of a PNG.

    If no ``IEND`` is found the chunk is simply appended.
    """
    iend_marker = b"IEND"
    # Search for the chunk type field "IEND"
    idx = png_data.rfind(iend_marker)
    if idx == -1:
        return png_data + chunk
    # The 4 bytes before IEND are its length field; we insert our chunk right
    # before the length field of IEND.
    insert_pos = idx - 4
    if insert_pos < 0:
        return png_data + chunk
    return png_data[:insert_pos] + chunk + png_data[insert_pos:]


def _remove_existing_ob_chunk(png_data: bytes) -> bytes:
    """Remove any existing ``openbadges`` tEXt chunk from *png_data*.

    Walks through all chunks and skips the first one whose keyword matches.
    """
    if png_data[:8] != PNG_SIGNATURE:
        raise ValueError("Not a valid PNG file (bad signature)")

    result = bytearray(png_data[:8])
    pos = 8

    ob_removed = False

    while pos + 8 <= len(png_data):
        length = struct.unpack(">I", png_data[pos:pos + 4])[0]
        chunk_type = png_data[pos + 4:pos + 8]

        chunk_start = pos
        chunk_end = pos + 4 + 4 + length + 4  # length + type + data + crc

        if chunk_end > len(png_data):
            break

        should_skip = False

        if chunk_type == b"tEXt" and not ob_removed:
            data = png_data[pos + 8:pos + 8 + length]
            nul_idx = data.find(b"\x00")
            if nul_idx != -1:
                kw = data[:nul_idx].decode("latin-1")
                if kw == OB_KEYWORD:
                    should_skip = True
                    ob_removed = True

        if not should_skip:
            result.extend(png_data[chunk_start:chunk_end])

        pos = chunk_end

    return bytes(result)


def bake_badge(png_path: Path | str, assertion: dict[str, Any]) -> bytes:
    """Embed *assertion* JSON into the PNG at *png_path*.

    Returns the raw bytes of the baked PNG.
    """
    png_path = Path(png_path)
    if not png_path.exists():
        raise FileNotFoundError(f"Badge PNG not found: {png_path}")

    png_data = png_path.read_bytes()
    png_data = _remove_existing_ob_chunk(png_data)

    assertion_json = json.dumps(assertion, ensure_ascii=False, indent=2)
    chunk = _make_text_chunk(OB_KEYWORD, assertion_json)

    return _insert_chunk_before_iend(png_data, chunk)


def bake_badge_from_bytes(png_data: bytes, assertion: dict[str, Any]) -> bytes:
    """Embed *assertion* JSON into raw PNG *png_data* (bytes).

    Useful when the PNG is provided from memory / upload rather than disk.
    """
    png_data = _remove_existing_ob_chunk(png_data)
    assertion_json = json.dumps(assertion, ensure_ascii=False, indent=2)
    chunk = _make_text_chunk(OB_KEYWORD, assertion_json)
    return _insert_chunk_before_iend(png_data, chunk)


# ---------------------------------------------------------------------------
# Unbaking — extract JSON from a baked PNG
# ---------------------------------------------------------------------------

def unbake_badge(png_data: bytes) -> dict[str, Any]:
    """Extract the Open Badges assertion JSON from a baked PNG.

    *png_data* can be raw bytes or a file path.
    Returns the parsed assertion dict.
    """
    if isinstance(png_data, (str, Path)):
        png_data = Path(png_data).read_bytes()

    if png_data[:8] != PNG_SIGNATURE:
        raise ValueError("Not a valid PNG file (bad signature)")

    pos = 8
    while pos + 8 <= len(png_data):
        length = struct.unpack(">I", png_data[pos:pos + 4])[0]
        chunk_type = png_data[pos + 4:pos + 8]

        chunk_end = pos + 4 + 4 + length + 4
        if chunk_end > len(png_data):
            break

        if chunk_type == b"tEXt":
            data = png_data[pos + 8:pos + 8 + length]
            nul_idx = data.find(b"\x00")
            if nul_idx != -1:
                kw = data[:nul_idx].decode("latin-1")
                if kw == OB_KEYWORD:
                    text = data[nul_idx + 1:].decode("utf-8")
                    return json.loads(text)

        pos = chunk_end

    raise ValueError("No Open Badges assertion found in this PNG")
