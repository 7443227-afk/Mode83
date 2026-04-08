from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "issued"


def issue_badge(name: str, email: str) -> dict:
    """Crée un badge, l'enregistre en JSON, puis retourne ses données."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    badge_data = {
        "id": str(uuid4()),
        "name": name,
        "email": email,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "title": "Badge 83",
        "issuer": "MODE83",
    }
    badge_path = DATA_DIR / f"{badge_data['id']}.json"
    with badge_path.open("w", encoding="utf-8") as file:
        json.dump(badge_data, file, ensure_ascii=False, indent=2)
    return badge_data
