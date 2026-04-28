from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_png_bytes() -> bytes:
    image = Image.new("RGBA", (256, 256), color=(240, 240, 240, 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def isolated_issuer_env(tmp_path, monkeypatch, sample_png_bytes):
    from app import config
    from app import issuer
    from app import verifier

    issued_dir = tmp_path / "issued"
    baked_dir = tmp_path / "baked"
    data_dir = tmp_path / "data"
    issued_dir.mkdir(parents=True, exist_ok=True)
    baked_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    issuer_template = data_dir / "issuer_template.json"
    badgeclass_template = data_dir / "badgeclass_template.json"
    badge_png = data_dir / "badge.png"

    issuer_template.write_text(
        json.dumps(
            {
                "@context": "https://w3id.org/openbadges/v2",
                "@language": "fr-FR",
                "id": "${BASE_URL}/issuers/main",
                "type": "Issuer",
                "name": "Mode83",
                "verification": {
                    "type": "VerificationObject",
                    "allowedOrigins": ["tests.mode83.local"],
                    "startsWith": ["${BASE_URL}/assertions/"],
                },
            }
        ),
        encoding="utf-8",
    )
    badgeclass_template.write_text(
        json.dumps(
            {
                "@context": "https://w3id.org/openbadges/v2",
                "@language": "fr-FR",
                "id": "${BASE_URL}/badges/blockchain-foundations",
                "type": "BadgeClass",
                "name": "Blockchain Foundations",
                "tags": ["mode83", "blockchain", "openbadges"],
                "alignment": [
                    {
                        "type": "AlignmentObject",
                        "targetName": "Parcours MODE83 — Fondamentaux Blockchain",
                        "targetDescription": "Référentiel pédagogique interne MODE83 pour l'initiation à la blockchain.",
                        "targetUrl": "${BASE_URL}",
                    }
                ],
                "issuer": "${BASE_URL}/issuers/main",
            }
        ),
        encoding="utf-8",
    )
    badge_png.write_bytes(sample_png_bytes)

    monkeypatch.setattr(config, "DATA_BASE", data_dir)
    monkeypatch.setattr(config, "ISSUED_DIR", issued_dir)
    monkeypatch.setattr(config, "BAKED_DIR", baked_dir)
    monkeypatch.setattr(config, "ISSUER_TEMPLATE", issuer_template)
    monkeypatch.setattr(config, "BADGECLASS_TEMPLATE", badgeclass_template)
    monkeypatch.setattr(config, "BADGE_PNG", badge_png)

    monkeypatch.setattr(issuer, "DATA_DIR", issued_dir)
    monkeypatch.setattr(issuer, "BAKED_DIR", baked_dir)
    monkeypatch.setattr(issuer, "ISSUER_TEMPLATE", issuer_template)
    monkeypatch.setattr(issuer, "BADGECLASS_TEMPLATE", badgeclass_template)
    monkeypatch.setattr(issuer, "BADGE_PNG", badge_png)
    monkeypatch.setattr(verifier, "DATA_DIR", issued_dir)

    monkeypatch.setenv("BADGE83_BASE_URL", "https://tests.mode83.local")
    monkeypatch.setenv("BADGE83_SEARCH_PEPPER", "test-pepper")

    return {
        "issued_dir": issued_dir,
        "baked_dir": baked_dir,
        "base_dir": data_dir,
        "issuer_template": issuer_template,
        "badgeclass_template": badgeclass_template,
        "badge_png": badge_png,
    }