from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "issued"


def verify_badge(badge_id: str) -> dict:
    """Vérifie si une Assertion Open Badges 2.0 existe et retourne son état avec ses données."""
    badge_path = DATA_DIR / f"{badge_id}.json"
    if not badge_path.exists():
        return {"valid": False, "assertion": None}

    with badge_path.open("r", encoding="utf-8") as file:
        badge_data = json.load(file)

    if badge_data.get("type") != "Assertion":
        return {"valid": False, "assertion": None}

    return {
        "valid": True,
        "assertion": badge_data,
        "summary": {
            "assertion_id": badge_id,
            "badge_name": badge_data.get("badge", {}).get("name"),
            "issuer_name": badge_data.get("issuer", {}).get("name"),
            "recipient_name": badge_data.get("recipient", {}).get("name"),
            "issued_on": badge_data.get("issuedOn"),
        },
    }
