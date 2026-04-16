#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def parse_itxt(data: bytes) -> dict[str, Any] | None:
    keyword_end = data.find(b"\x00")
    if keyword_end == -1:
        return None

    keyword = data[:keyword_end].decode("latin-1", errors="replace")
    rest = data[keyword_end + 1 :]
    if len(rest) < 2:
        return None

    compression_flag = rest[0]
    compression_method = rest[1]
    rest = rest[2:]

    language_end = rest.find(b"\x00")
    if language_end == -1:
        return None
    language = rest[:language_end].decode("latin-1", errors="replace")
    rest = rest[language_end + 1 :]

    translated_end = rest.find(b"\x00")
    if translated_end == -1:
        return None
    translated_keyword = rest[:translated_end].decode("utf-8", errors="replace")
    text_bytes = rest[translated_end + 1 :]

    if compression_flag == 1:
        if compression_method != 0:
            return None
        text_bytes = zlib.decompress(text_bytes)
    elif compression_flag != 0:
        return None

    return {
        "keyword": keyword,
        "compression_flag": compression_flag,
        "compression_method": compression_method,
        "language": language,
        "translated_keyword": translated_keyword,
        "text": text_bytes.decode("utf-8", errors="replace"),
    }


def try_parse_json(text: str) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(text)
    except Exception:
        return None


def inspect_png(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    report: dict[str, Any] = {
        "file": path.name,
        "path": str(path),
        "size_bytes": len(data),
        "signature_ok": data[:8] == PNG_SIGNATURE,
        "chunk_count": 0,
        "chunk_summary": {},
        "chunks": [],
        "openbadges_injections": [],
    }

    pos = 8
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8].decode("latin-1", errors="replace")
        payload = data[pos + 8 : pos + 8 + length]
        chunk: dict[str, Any] = {
            "index": report["chunk_count"] + 1,
            "type": chunk_type,
            "length": length,
        }

        if chunk_type == "tEXt":
            nul_idx = payload.find(b"\x00")
            if nul_idx != -1:
                keyword = payload[:nul_idx].decode("latin-1", errors="replace")
                text = payload[nul_idx + 1 :].decode("utf-8", errors="replace")
                chunk["keyword"] = keyword
                chunk["text_preview"] = text[:160]
                parsed_json = try_parse_json(text)
                if parsed_json is not None:
                    chunk["json_keys"] = list(parsed_json.keys()) if isinstance(parsed_json, dict) else None
                if keyword == "openbadges":
                    report["openbadges_injections"].append(
                        {
                            "chunk_type": "tEXt",
                            "keyword": keyword,
                            "parsed_json": parsed_json,
                            "raw_text": text,
                        }
                    )

        elif chunk_type == "iTXt":
            parsed = parse_itxt(payload)
            if parsed is not None:
                chunk.update({k: v for k, v in parsed.items() if k != "text"})
                chunk["text_preview"] = parsed["text"][:160]
                parsed_json = try_parse_json(parsed["text"])
                if parsed_json is not None:
                    chunk["json_keys"] = list(parsed_json.keys()) if isinstance(parsed_json, dict) else None
                if parsed["keyword"] == "openbadges":
                    report["openbadges_injections"].append(
                        {
                            "chunk_type": "iTXt",
                            "keyword": parsed["keyword"],
                            "compression_flag": parsed["compression_flag"],
                            "parsed_json": parsed_json,
                            "raw_text": parsed["text"],
                        }
                    )

        report["chunks"].append(chunk)
        report["chunk_count"] += 1
        report["chunk_summary"][chunk_type] = report["chunk_summary"].get(chunk_type, 0) + 1

        pos += 12 + length
        if chunk_type == "IEND":
            break

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspecte un PNG et produit un rapport de structure et de métadonnées Open Badges."
    )
    parser.add_argument("png_file", help="Chemin du fichier PNG à analyser")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Affiche le JSON avec indentation",
    )
    args = parser.parse_args()

    path = Path(args.png_file)
    if not path.exists():
        print(f"Fichier introuvable : {path}", file=sys.stderr)
        return 1

    report = inspect_png(path)
    if args.pretty:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())