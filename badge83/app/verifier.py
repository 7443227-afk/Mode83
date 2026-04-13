from __future__ import annotations

import json
from pathlib import Path

from app.baker import unbake_badge

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

    badge_ref = badge_data.get("badge", "")
    issuer_ref = badge_data.get("issuer", "")

    # Handle both URL references (string) and embedded objects (dict)
    if isinstance(badge_ref, str):
        badge_name = badge_ref.split("/")[-1].replace("-", " ").title()
    else:
        badge_name = badge_ref.get("name", "unknown")

    if isinstance(issuer_ref, str):
        issuer_name = issuer_ref.split("/")[-1].replace("-", " ").title()
    else:
        issuer_name = issuer_ref.get("name", "unknown")

    return {
        "valid": True,
        "assertion": badge_data,
        "summary": {
            "assertion_id": badge_id,
            "badge_name": badge_name,
            "issuer_name": issuer_name,
            "recipient_name": badge_data.get("recipient", {}).get("name", "unknown"),
            "issued_on": badge_data.get("issuedOn"),
        },
    }


def verify_baked_badge(png_data: bytes) -> dict:
    """Extrait l'assertion d'un PNG baked et la vérifie."""
    try:
        assertion = unbake_badge(png_data)
    except (ValueError, Exception) as exc:
        return {"valid": False, "error": str(exc), "assertion": None}

    if assertion.get("type") != "Assertion":
        return {"valid": False, "error": "Not a valid Open Badges Assertion", "assertion": None}

    badge_id = assertion.get("id", "unknown")
    badge_ref = assertion.get("badge", "")
    issuer_ref = assertion.get("issuer", "")

    # Handle both URL references (string) and embedded objects (dict)
    if isinstance(badge_ref, str):
        badge_name = badge_ref.split("/")[-1].replace("-", " ").title()
    else:
        badge_name = badge_ref.get("name", "unknown")

    if isinstance(issuer_ref, str):
        issuer_name = issuer_ref.split("/")[-1].replace("-", " ").title()
    else:
        issuer_name = issuer_ref.get("name", "unknown")

    return {
        "valid": True,
        "assertion": assertion,
        "summary": {
            "assertion_id": badge_id,
            "badge_name": badge_name,
            "issuer_name": issuer_name,
            "recipient_name": assertion.get("recipient", {}).get("name", "unknown"),
            "issued_on": assertion.get("issuedOn"),
        },
    }
