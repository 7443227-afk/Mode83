from __future__ import annotations

import json
from hashlib import sha256
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.baker import bake_badge, bake_badge_from_bytes

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "issued"
BAKED_DIR = Path(__file__).resolve().parent.parent / "data" / "baked"
BASE_DIR = Path(__file__).resolve().parent.parent / "data"
ISSUER_FILE = BASE_DIR / "issuer.json"
BADGECLASS_FILE = BASE_DIR / "badgeclass.json"
BADGE_PNG = BASE_DIR / "badge.png"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _recipient_identity(email: str) -> str:
    return sha256(email.strip().lower().encode("utf-8")).hexdigest()


def issue_badge(name: str, email: str) -> dict:
    """Crée une Assertion Open Badges minimale, l'enregistre en JSON, puis la retourne."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    issuer = _load_json(ISSUER_FILE)
    badgeclass = _load_json(BADGECLASS_FILE)

    assertion_id = str(uuid4())
    issued_on = datetime.now(timezone.utc).isoformat()

    badge_data = {
        "@context": "https://w3id.org/openbadges/v2",
        "id": f"urn:uuid:{assertion_id}",
        "type": "Assertion",
        "recipient": {
            "type": "email",
            "hashed": True,
            "identity": _recipient_identity(email),
            "plaintext_email": email,
            "name": name,
        },
        "issuedOn": issued_on,
        "verification": {
            "type": "HostedBadge"
        },
        "badge": badgeclass,
        "issuer": issuer,
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
    """Crée une Assertion Open Badges, la bake dans un PNG et la sauvegarde.

    Si *png_data* est fourni (upload), il est utilisé comme base.
    Sinon, le PNG par défaut ``data/badge.png`` est utilisé.

    Retourne un dictionnaire contenant l'assertion, le PNG baké (bytes),
    et les métadonnées associées.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BAKED_DIR.mkdir(parents=True, exist_ok=True)

    issuer = _load_json(ISSUER_FILE)
    badgeclass = _load_json(BADGECLASS_FILE)

    assertion_id = str(uuid4())
    issued_on = datetime.now(timezone.utc).isoformat()

    assertion = {
        "@context": "https://w3id.org/openbadges/v2",
        "id": f"urn:uuid:{assertion_id}",
        "type": "Assertion",
        "recipient": {
            "type": "email",
            "hashed": True,
            "identity": _recipient_identity(email),
            "plaintext_email": email,
            "name": name,
        },
        "issuedOn": issued_on,
        "verification": {
            "type": "HostedBadge"
        },
        "badge": badgeclass,
        "issuer": issuer,
    }

    # Save JSON assertion
    badge_path = DATA_DIR / f"{assertion_id}.json"
    with badge_path.open("w", encoding="utf-8") as file:
        json.dump(assertion, file, ensure_ascii=False, indent=2)

    # Bake into PNG
    if png_data:
        baked_png = bake_badge_from_bytes(png_data, assertion)
    else:
        baked_png = bake_badge(BADGE_PNG, assertion)

    baked_path = BAKED_DIR / f"{assertion_id}.png"
    baked_path.write_bytes(baked_png)

    return {
        "assertion_id": assertion_id,
        "assertion": assertion,
        "baked_png_path": str(baked_path),
        "baked_png_bytes": baked_png,
        "issuer": issuer,
        "badgeclass": badgeclass,
    }
