"""
Utilitaires de baking / unbaking PNG pour Open Badges.

Baking = injection d'une assertion JSON dans un PNG via un chunk texte
avec le mot-clé ``openbadges`` (selon la spécification Open Badges).

Pour maximiser la compatibilité avec les validateurs externes Open Badges 2.0,
les nouveaux badges sont désormais bakés via un chunk ``tEXt``. L'unbaking
reste compatible avec ``tEXt`` et ``iTXt`` afin de continuer à lire les badges
déjà émis avec l'ancien format.
"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path
from typing import Any

# Signature PNG : 8 octets
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# Mot-clé utilisé dans le chunk texte PNG selon la spécification Open Badges
OB_KEYWORD = "openbadges"


# ---------------------------------------------------------------------------
# Baking — injection du JSON dans un PNG
# ---------------------------------------------------------------------------

def _make_text_chunk(keyword: str, text: str) -> bytes:
    """Construit un chunk PNG ``tEXt`` hérité.

    Format :  length (4B) | type (4B) | keyword | NUL | text | CRC (4B)
    """
    payload = keyword.encode("latin-1") + b"\x00" + text.encode("utf-8")
    chunk_type = b"tEXt"
    crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def _make_itxt_chunk(keyword: str, text: str) -> bytes:
    """Construit un chunk PNG ``iTXt`` avec du texte UTF-8.

    Format iTXt :
      keyword\\x00 compression_flag compression_method language_tag\\x00
      translated_keyword\\x00 text

    Le texte UTF-8 est stocké non compressé avec les champs langue/traduction vides.
    """
    payload = (
        keyword.encode("latin-1")
        + b"\x00"                # terminateur du mot-clé
        + b"\x00"                # flag de compression : 0 = non compressé
        + b"\x00"                # méthode de compression
        + b"\x00"                # tag de langue vide
        + b"\x00"                # mot-clé traduit vide
        + text.encode("utf-8")
    )
    chunk_type = b"iTXt"
    crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def _insert_chunk_before_iend(png_data: bytes, chunk: bytes) -> bytes:
    """Insère *chunk* juste avant le chunk ``IEND`` d'un PNG.

    Si aucun ``IEND`` n'est trouvé, le chunk est simplement ajouté à la fin.
    """
    iend_marker = b"IEND"
    # Recherche du champ type "IEND"
    idx = png_data.rfind(iend_marker)
    if idx == -1:
        return png_data + chunk
    # Les 4 octets avant IEND sont son champ length ; on insère notre chunk
    # juste avant ce champ length.
    insert_pos = idx - 4
    if insert_pos < 0:
        return png_data + chunk
    return png_data[:insert_pos] + chunk + png_data[insert_pos:]


def _remove_existing_ob_chunk(png_data: bytes) -> bytes:
    """Supprime tout chunk texte ``openbadges`` existant de *png_data*.

    Parcourt tous les chunks et retire tout chunk ``tEXt`` ou ``iTXt`` dont
    le mot-clé correspond à ``openbadges``.
    """
    if png_data[:8] != PNG_SIGNATURE:
        raise ValueError("Fichier PNG invalide (signature incorrecte)")

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

        if chunk_type in (b"tEXt", b"iTXt"):
            data = png_data[pos + 8:pos + 8 + length]

            if chunk_type == b"tEXt":
                nul_idx = data.find(b"\x00")
                if nul_idx != -1:
                    kw = data[:nul_idx].decode("latin-1")
                    if kw == OB_KEYWORD:
                        should_skip = True
                        ob_removed = True

            elif chunk_type == b"iTXt":
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
    """Injecte le JSON de l'*assertion* dans le PNG à *png_path*.

    Retourne les octets bruts du PNG baké.
    """
    png_path = Path(png_path)
    if not png_path.exists():
        raise FileNotFoundError(f"Image PNG introuvable : {png_path}")

    png_data = png_path.read_bytes()
    png_data = _remove_existing_ob_chunk(png_data)

    assertion_json = json.dumps(assertion, ensure_ascii=False, separators=(",", ":"))
    chunk = _make_text_chunk(OB_KEYWORD, assertion_json)

    return _insert_chunk_before_iend(png_data, chunk)


def bake_badge_from_bytes(png_data: bytes, assertion: dict[str, Any]) -> bytes:
    """Injecte le JSON de l'*assertion* dans un PNG brut *png_data* (octets).

    Utile lorsque le PNG est fourni en mémoire / via un upload plutôt que
    depuis le disque.
    """
    png_data = _remove_existing_ob_chunk(png_data)
    assertion_json = json.dumps(assertion, ensure_ascii=False, separators=(",", ":"))
    chunk = _make_text_chunk(OB_KEYWORD, assertion_json)
    return _insert_chunk_before_iend(png_data, chunk)


# ---------------------------------------------------------------------------
# Unbaking — extraction du JSON depuis un PNG baké
# ---------------------------------------------------------------------------

def _extract_text_from_itxt(data: bytes) -> tuple[str, str] | None:
    """Analyse le payload d'un chunk ``iTXt`` et retourne ``(keyword, text)``.

    Retourne ``None`` si le payload est malformé.
    """
    keyword_end = data.find(b"\x00")
    if keyword_end == -1:
        return None

    try:
        keyword = data[:keyword_end].decode("latin-1")
    except UnicodeDecodeError:
        return None

    rest = data[keyword_end + 1:]
    if len(rest) < 3:
        return None

    compression_flag = rest[0]
    compression_method = rest[1]
    rest = rest[2:]

    lang_end = rest.find(b"\x00")
    if lang_end == -1:
        return None
    rest = rest[lang_end + 1:]

    translated_end = rest.find(b"\x00")
    if translated_end == -1:
        return None
    text_bytes = rest[translated_end + 1:]

    if compression_flag == 1:
        if compression_method != 0:
            return None
        try:
            text_bytes = zlib.decompress(text_bytes)
        except zlib.error:
            return None
    elif compression_flag != 0:
        return None

    try:
        text = text_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None

    return keyword, text


def unbake_badge(png_data: bytes) -> dict[str, Any]:
    """Extrait le JSON de l'assertion Open Badges depuis un PNG baké.

    *png_data* peut être des octets bruts ou un chemin de fichier.
    Retourne le dictionnaire d'assertion parsé.
    """
    if isinstance(png_data, (str, Path)):
        png_data = Path(png_data).read_bytes()

    if png_data[:8] != PNG_SIGNATURE:
        raise ValueError("Fichier PNG invalide (signature incorrecte)")

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

        elif chunk_type == b"iTXt":
            data = png_data[pos + 8:pos + 8 + length]
            parsed = _extract_text_from_itxt(data)
            if parsed is not None:
                kw, text = parsed
                if kw == OB_KEYWORD:
                    return json.loads(text)

        pos = chunk_end

    raise ValueError("Aucune assertion Open Badges trouvée dans ce PNG")
