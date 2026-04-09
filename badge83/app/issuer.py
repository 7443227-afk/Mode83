from __future__ import annotations

import json
from hashlib import sha256
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "issued"
BASE_DIR = Path(__file__).resolve().parent.parent / "data"
ISSUER_FILE = BASE_DIR / "issuer.json"
BADGECLASS_FILE = BASE_DIR / "badgeclass.json"


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
