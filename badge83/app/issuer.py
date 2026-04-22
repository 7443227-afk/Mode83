from __future__ import annotations

import json
import secrets
from hashlib import sha256
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.baker import bake_badge, bake_badge_from_bytes
from app.config import (
    BAKED_DIR,
    BADGE_PNG,
    BADGECLASS_TEMPLATE,
    DEFAULT_BASE_URL,
    ISSUED_DIR as DATA_DIR,
    ISSUER_TEMPLATE,
    get_public_base_url,
    get_search_pepper,
)
from app.qr import make_verification_qr_url, overlay_qr_on_badge


def _compose_public_base_url() -> str:
    return get_public_base_url()


def get_base_url() -> str:
    return _compose_public_base_url() or DEFAULT_BASE_URL


def _build_baked_download_filename(issued_on: str) -> str:
    try:
        parsed = datetime.fromisoformat(issued_on.replace("Z", "+00:00"))
        date_part = parsed.strftime("%d%m%y")
    except Exception:
        date_part = datetime.now(timezone.utc).strftime("%d%m%y")

    BAKED_DIR.mkdir(parents=True, exist_ok=True)
    existing_files = sorted(path for path in BAKED_DIR.glob("*.png"))
    sequence = len(existing_files) + 1
    return f"{sequence}_mode83_{date_part}.png"


def _load_template(path: Path) -> dict:
    """Charge un template JSON et remplace ${BASE_URL} par la valeur réelle."""
    content = path.read_text(encoding="utf-8")
    content = content.replace("${BASE_URL}", get_base_url())
    return json.loads(content)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _make_recipient_hash(email: str, salt: str) -> str:
    normalized_email = email.strip().lower().encode("utf-8")
    return "sha256$" + sha256(normalized_email + salt.encode("utf-8")).hexdigest()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def make_search_hash(value: str) -> str:
    normalized_value = value.encode("utf-8")
    return "sha256$" + sha256(normalized_value + get_search_pepper().encode("utf-8")).hexdigest()


def make_search_metadata(name: str, email: str) -> dict:
    return {
        "name_hash": make_search_hash(normalize_name(name)),
        "email_hash": make_search_hash(normalize_email(email)),
    }


def make_admin_recipient_metadata(name: str, email: str) -> dict:
    return {
        "name": name.strip(),
        "email": normalize_email(email),
    }


def _make_recipient(email: str) -> dict:
    salt = secrets.token_hex(8)
    return {
        "type": "email",
        "hashed": True,
        "salt": salt,
        "identity": _make_recipient_hash(email, salt),
    }


def issue_badge(name: str, email: str) -> dict:
    """Crée une assertion Open Badges minimale, l'enregistre en JSON, puis la retourne."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    issuer = _load_template(ISSUER_TEMPLATE)
    badgeclass = _load_template(BADGECLASS_TEMPLATE)

    assertion_id = str(uuid4())
    issued_on = datetime.now(timezone.utc).isoformat()

    # URLs de référence pour HostedBadge
    base_url = get_base_url()
    issuer_url = f"{base_url}/issuers/main"
    badge_url = f"{base_url}/badges/blockchain-foundations"
    assertion_url = f"{base_url}/assertions/{assertion_id}"

    badge_data = {
        "@context": "https://w3id.org/openbadges/v2",
        "id": assertion_url,
        "type": "Assertion",
        "url": assertion_url,
        "recipient": _make_recipient(email),
        "issuedOn": issued_on,
        "verification": {
            "type": "HostedBadge",
            "url": assertion_url,
        },
        "badge": badge_url,
        "issuer": issuer_url,
        "admin_recipient": make_admin_recipient_metadata(name=name, email=email),
        "search": make_search_metadata(name=name, email=email),
    }

    badge_path = DATA_DIR / f"{assertion_id}.json"
    with badge_path.open("w", encoding="utf-8") as file:
        json.dump(badge_data, file, ensure_ascii=False, indent=2)

    return {
        "assertion_id": assertion_id,
        "assertion": badge_data,
        "issuer": issuer,
        "badgeclass": badgeclass,
    }


def issue_baked_badge(name: str, email: str, png_data: bytes | None = None) -> dict:
    """Crée une assertion Open Badges, la bake dans un PNG et la sauvegarde.

    Si *png_data* est fourni (upload), il est utilisé comme base.
    Sinon, le PNG par défaut ``data/badge.png`` est utilisé.

    Retourne un dictionnaire contenant l'assertion, le PNG baké (bytes),
    et les métadonnées associées.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BAKED_DIR.mkdir(parents=True, exist_ok=True)

    issuer = _load_template(ISSUER_TEMPLATE)
    badgeclass = _load_template(BADGECLASS_TEMPLATE)

    assertion_id = str(uuid4())
    issued_on = datetime.now(timezone.utc).isoformat()
    baked_download_filename = _build_baked_download_filename(issued_on)

    # URLs de référence pour HostedBadge
    base_url = get_base_url()
    issuer_url = f"{base_url}/issuers/main"
    badge_url = f"{base_url}/badges/blockchain-foundations"
    assertion_url = f"{base_url}/assertions/{assertion_id}"
    verification_page_url = make_verification_qr_url(base_url, assertion_id)

    assertion = {
        "@context": "https://w3id.org/openbadges/v2",
        "id": assertion_url,
        "type": "Assertion",
        "url": assertion_url,
        "recipient": _make_recipient(email),
        "issuedOn": issued_on,
        "verification": {
            "type": "HostedBadge",
            "url": assertion_url,
        },
        "badge": badge_url,
        "issuer": issuer_url,
        "admin_recipient": make_admin_recipient_metadata(name=name, email=email),
        "search": make_search_metadata(name=name, email=email),
    }

    # Sauvegarde de l'assertion JSON
    badge_path = DATA_DIR / f"{assertion_id}.json"
    with badge_path.open("w", encoding="utf-8") as file:
        json.dump(assertion, file, ensure_ascii=False, indent=2)

    # Composition visuelle du badge avec QR avant baking Open Badges.
    if png_data:
        source_png = png_data
    else:
        source_png = BADGE_PNG.read_bytes()

    qr_ready_png = overlay_qr_on_badge(source_png, verification_page_url)
    baked_png = bake_badge_from_bytes(qr_ready_png, assertion)

    baked_path = BAKED_DIR / f"{assertion_id}.png"
    baked_path.write_bytes(baked_png)

    return {
        "assertion_id": assertion_id,
        "assertion": assertion,
        "baked_png_path": str(baked_path),
        "baked_download_filename": baked_download_filename,
        "baked_png_bytes": baked_png,
        "verification_page_url": verification_page_url,
        "issuer": issuer,
        "badgeclass": badgeclass,
    }
