from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "issued"


def verify_badge(badge_id: str) -> dict:
    """Vérifie si un badge existe et retourne son état avec ses données."""
    badge_path = DATA_DIR / f"{badge_id}.json"
    if not badge_path.exists():
        return {"valid": False, "badge": None}

    with badge_path.open("r", encoding="utf-8") as file:
        badge_data = json.load(file)

    return {"valid": True, "badge": badge_data}
