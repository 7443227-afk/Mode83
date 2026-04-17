from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx

from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from fastapi.templating import Jinja2Templates

from app.issuer import issue_badge, issue_baked_badge
from app.verifier import verify_badge, verify_baked_badge

app = FastAPI(title="Badge 83")
templates = Jinja2Templates(directory="templates")
DATA_BASE = Path(__file__).resolve().parent.parent / "data"
ISSUED_DIR = DATA_BASE / "issued"
BAKED_DIR = DATA_BASE / "baked"

# ---------------------------------------------------------------------------
# Base URL configuration (via environment variable)
# ---------------------------------------------------------------------------
BASE_URL = os.environ.get("BADGE83_BASE_URL", "http://127.0.0.1:8000")
OB_CONTENT_TYPE = 'application/ld+json; profile="https://w3id.org/openbadges/v2"'

# ---------------------------------------------------------------------------
# CORS — allow external validators (e.g. validator.openbadges.org) to fetch resources
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Affiche la nouvelle console d'administration Badge83."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/legacy", response_class=HTMLResponse)
async def legacy_index(request: Request):
    """Affiche l'ancienne interface pour rollback rapide."""
    return templates.TemplateResponse("index_legacy.html", {"request": request})


@app.get("/badge.png")
async def get_badge_png():
    """Télécharge l'image badge par défaut (pour baking local ou référence)."""
    return FileResponse(DATA_BASE / "badge.png", media_type="image/png")


@app.post("/issue")
async def issue(name: str = Form(...), email: str = Form(...)):
    """Reçoit les informations utilisateur et émet une Assertion Open Badges."""
    badge = issue_badge(name=name, email=email)
    return {"status": "issued", "badge": badge}


@app.post("/issue-baked")
async def issue_baked(name: str = Form(...), email: str = Form(...), badge_image: UploadFile | None = File(None)):
    """Émet un badge Open Badges baked dans un PNG.

    Si *badge_image* est fourni (upload), il est utilisé comme base.
    Sinon le PNG par défaut ``data/badge.png`` est utilisé.
    """
    png_data = await badge_image.read() if badge_image else None
    result = issue_baked_badge(name=name, email=email, png_data=png_data)
    return Response(
        content=result["baked_png_bytes"],
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="badge-{result["assertion_id"]}.png"',
        },
    )


@app.get("/verify/{badge_id}")
async def verify(badge_id: str):
    """Vérifie l'existence d'une Assertion Open Badges via son identifiant."""
    result = verify_badge(badge_id=badge_id)
    return result


@app.get("/verify")
async def verify_query(badge_id: str):
    """Permet la vérification via query string (?badge_id=...)."""
    result = verify_badge(badge_id=badge_id)
    return result


@app.post("/verify-baked")
async def verify_baked(badge: UploadFile = File(...)):
    """Vérifie un badge Open Badges à partir d'un PNG baked uploadé."""
    png_data = await badge.read()
    result = verify_baked_badge(png_data)
    return result


def _extract_assertion_id(assertion: dict[str, Any]) -> str:
    assertion_id = assertion.get("id", "")
    if isinstance(assertion_id, str) and "/" in assertion_id:
        return assertion_id.rstrip("/").split("/")[-1]
    return str(assertion_id or "unknown")


def _safe_load_json(file_path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _collect_badge_record(assertion_id: str, assertion: dict[str, Any] | None = None) -> dict[str, Any] | None:
    json_path = ISSUED_DIR / f"{assertion_id}.json"
    png_path = BAKED_DIR / f"{assertion_id}.png"

    if assertion is None and json_path.exists():
        assertion = _safe_load_json(json_path)

    if assertion is None:
        return None

    recipient = assertion.get("recipient", {}) if isinstance(assertion.get("recipient"), dict) else {}
    verification = assertion.get("verification", {}) if isinstance(assertion.get("verification"), dict) else {}

    badge_ref = assertion.get("badge", "")
    issuer_ref = assertion.get("issuer", "")
    badge_name = badge_ref.split("/")[-1].replace("-", " ").title() if isinstance(badge_ref, str) and badge_ref else "Unknown"
    issuer_name = issuer_ref.split("/")[-1].replace("-", " ").title() if isinstance(issuer_ref, str) and issuer_ref else "Unknown"

    return {
        "assertion_id": assertion_id,
        "issued_on": assertion.get("issuedOn"),
        "has_json": json_path.exists(),
        "has_png": png_path.exists(),
        "json_url": f"/api/badges/{assertion_id}/json",
        "png_url": f"/api/badges/{assertion_id}/png",
        "public_assertion_url": assertion.get("url") or assertion.get("id"),
        "badge_name": badge_name,
        "issuer_name": issuer_name,
        "recipient": {
            "type": recipient.get("type"),
            "identity": recipient.get("identity"),
            "hashed": recipient.get("hashed"),
            "salt": recipient.get("salt"),
        },
        "verification": verification,
        "assertion": assertion,
    }


def _list_badge_records() -> list[dict[str, Any]]:
    ISSUED_DIR.mkdir(parents=True, exist_ok=True)
    BAKED_DIR.mkdir(parents=True, exist_ok=True)

    assertion_ids = {path.stem for path in ISSUED_DIR.glob("*.json")}
    assertion_ids.update(path.stem for path in BAKED_DIR.glob("*.png"))

    records: list[dict[str, Any]] = []
    for assertion_id in sorted(assertion_ids):
        record = _collect_badge_record(assertion_id)
        if record:
            records.append(record)

    records.sort(key=lambda item: item.get("issued_on") or "", reverse=True)
    return records


def _dashboard_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    hosted_count = sum(1 for record in records if str(record.get("public_assertion_url", "")).startswith("http"))
    return {
        "total_badges": len(records),
        "total_json": sum(1 for record in records if record.get("has_json")),
        "total_png": sum(1 for record in records if record.get("has_png")),
        "hosted_ready": hosted_count,
        "base_url": BASE_URL,
        "latest_badge": records[0]["assertion_id"] if records else None,
    }


@app.get("/api/dashboard/stats")
async def api_dashboard_stats():
    records = _list_badge_records()
    return _dashboard_stats(records)


@app.get("/api/badges")
async def api_list_badges():
    records = _list_badge_records()
    return {"items": records, "stats": _dashboard_stats(records)}


@app.get("/api/badges/{assertion_id}")
async def api_get_badge(assertion_id: str):
    record = _collect_badge_record(assertion_id)
    if not record:
        raise HTTPException(status_code=404, detail="Badge not found")

    png_inspection = None
    png_path = BAKED_DIR / f"{assertion_id}.png"
    if png_path.exists():
        png_inspection = verify_baked_badge(png_path.read_bytes())

    return {
        **record,
        "png_preview_url": record["png_url"] if record.get("has_png") else None,
        "png_inspection": png_inspection,
    }


@app.get("/api/badges/{assertion_id}/json")
async def api_download_badge_json(assertion_id: str):
    file_path = ISSUED_DIR / f"{assertion_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Badge JSON not found")
    return FileResponse(file_path, media_type="application/json", filename=f"{assertion_id}.json")


@app.get("/api/badges/{assertion_id}/png")
async def api_download_badge_png(assertion_id: str):
    file_path = BAKED_DIR / f"{assertion_id}.png"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Badge PNG not found")
    return FileResponse(file_path, media_type="image/png", filename=f"{assertion_id}.png")


@app.get("/api/badges/{assertion_id}/inspect")
async def api_inspect_badge_png(assertion_id: str):
    file_path = BAKED_DIR / f"{assertion_id}.png"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Badge PNG not found")
    return verify_baked_badge(file_path.read_bytes())


@app.put("/api/badges/{assertion_id}")
async def api_update_badge(assertion_id: str, payload: dict[str, Any] = Body(...)):
    file_path = ISSUED_DIR / f"{assertion_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Badge not found")

    assertion = _safe_load_json(file_path)
    if not assertion or assertion.get("type") != "Assertion":
        raise HTTPException(status_code=400, detail="Invalid badge assertion")

    updated_assertion = payload.get("assertion") if isinstance(payload.get("assertion"), dict) else payload
    if updated_assertion.get("type") != "Assertion":
        raise HTTPException(status_code=400, detail="Payload must be an Open Badges Assertion")

    updated_assertion["id"] = assertion.get("id")
    if assertion.get("url"):
        updated_assertion["url"] = assertion.get("url")

    file_path.write_text(json.dumps(updated_assertion, ensure_ascii=False, indent=2), encoding="utf-8")
    record = _collect_badge_record(assertion_id, updated_assertion)
    return {"status": "updated", "item": record}


@app.delete("/api/badges/{assertion_id}")
async def api_delete_badge(assertion_id: str):
    json_path = ISSUED_DIR / f"{assertion_id}.json"
    png_path = BAKED_DIR / f"{assertion_id}.png"

    deleted = []
    if json_path.exists():
        json_path.unlink()
        deleted.append("json")
    if png_path.exists():
        png_path.unlink()
        deleted.append("png")

    if not deleted:
        raise HTTPException(status_code=404, detail="Badge not found")

    return {"status": "deleted", "assertion_id": assertion_id, "deleted": deleted}


# ---------------------------------------------------------------------------
# Public endpoints for HostedBadge verification (Open Badges 2.0)
# ---------------------------------------------------------------------------

def _serve_json_file(file_path: Path) -> JSONResponse:
    """Helper to serve a JSON file with the correct Open Badges content type."""
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"error": "Resource not found"})
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return JSONResponse(content=data, media_type=OB_CONTENT_TYPE)


def _serve_template_json(template_name: str) -> JSONResponse:
    """Serve a JSON template file with ${BASE_URL} placeholder replaced."""
    template_path = DATA_BASE / template_name
    if not template_path.exists():
        return JSONResponse(status_code=404, content={"error": "Resource not found"})
    content = template_path.read_text(encoding="utf-8")
    content = content.replace("${BASE_URL}", BASE_URL)
    data = json.loads(content)
    return JSONResponse(content=data, media_type=OB_CONTENT_TYPE)


@app.get("/issuers/{issuer_id}")
async def get_issuer(issuer_id: str):
    """Sert le profil de l'émetteur à une URL publique.

    URL attendue : {BASE_URL}/issuers/main
    """
    return _serve_template_json("issuer_template.json")


@app.get("/badges/{badge_slug}")
async def get_badge_class(badge_slug: str):
    """Sert la définition du badge à une URL publique.

    URL attendue : {BASE_URL}/badges/blockchain-foundations
    """
    return _serve_template_json("badgeclass_template.json")


@app.get("/assertions/{assertion_id}")
async def get_assertion(assertion_id: str):
    """Sert une assertion Open Badges à une URL publique.

    URL attendue : {BASE_URL}/assertions/<uuid>
    """
    return _serve_json_file(DATA_BASE / "issued" / f"{assertion_id}.json")


@app.get("/assets/{asset_name}")
async def get_asset(asset_name: str):
    """Sert les assets statiques (images de badge, logo émetteur, etc.)."""
    asset_path = DATA_BASE / asset_name
    if not asset_path.exists():
        return JSONResponse(status_code=404, content={"error": "Asset not found"})
    return FileResponse(asset_path, media_type="image/png")


# ---------------------------------------------------------------------------
# Online verification — resolve public URLs and validate the full chain
# ---------------------------------------------------------------------------

async def _fetch_url(url: str) -> dict | None:
    """Fetch a URL and return parsed JSON, or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                return None
            return resp.json()
    except Exception:
        return None


@app.post("/verify-online")
async def verify_online(
    assertion_url: str | None = Form(None),
    badge_file: UploadFile | None = File(None),
):
    """Vérifie un badge en résolvant toutes les URLs publiques de la chaîne.

    Accepte soit une URL d'assertion, soit un fichier PNG baked.
    Retourne l'assertion + l'état de chaque ressource référencée.
    """
    assertion = None

    # Case 1: user uploaded a baked PNG
    if badge_file:
        png_data = await badge_file.read()
        from app.verifier import verify_baked_badge
        result = verify_baked_badge(png_data)
        if not result["valid"]:
            return {"valid": False, "error": result.get("error", "Failed to extract assertion")}
        assertion = result["assertion"]

    # Case 2: user provided an assertion URL
    elif assertion_url:
        assertion = await _fetch_url(assertion_url)
        if not assertion or assertion.get("type") != "Assertion":
            return {"valid": False, "error": "Unable to fetch a valid Assertion from this URL"}
    else:
        return JSONResponse(
            status_code=400,
            content={"error": "Provide either assertion_url or badge_file"},
        )

    # Resolve the full chain: badge URL → BadgeClass, issuer URL → Issuer
    badge_ref = assertion.get("badge", "")
    issuer_ref = assertion.get("issuer", "")

    badge_data = None
    issuer_data = None

    if isinstance(badge_ref, str) and badge_ref.startswith("http"):
        badge_data = await _fetch_url(badge_ref)
    if isinstance(issuer_ref, str) and issuer_ref.startswith("http"):
        issuer_data = await _fetch_url(issuer_ref)

    # Cross-check: BadgeClass.issuer should match assertion.issuer
    chain_valid = True
    chain_notes = []

    if badge_data is None and isinstance(badge_ref, str):
        chain_valid = False
        chain_notes.append(f"BadgeClass inaccessible: {badge_ref}")
    if issuer_data is None and isinstance(issuer_ref, str):
        chain_valid = False
        chain_notes.append(f"Issuer inaccessible: {issuer_ref}")

    if badge_data and issuer_ref:
        badge_issuer = badge_data.get("issuer", "")
        if isinstance(badge_issuer, str) and badge_issuer != issuer_ref:
            chain_valid = False
            chain_notes.append("BadgeClass.issuer ne correspond pas à assertion.issuer")

    if not chain_notes:
        chain_notes.append("Chaîne complète validée")

    return {
        "valid": chain_valid,
        "assertion": assertion,
        "chain": {
            "badge_class": badge_data,
            "issuer": issuer_data,
            "notes": chain_notes,
        },
        "summary": {
            "assertion_id": assertion.get("id", "unknown"),
            "badge_name": badge_ref.split("/")[-1].replace("-", " ").title() if isinstance(badge_ref, str) else "unknown",
            "issuer_name": issuer_ref.split("/")[-1].title() if isinstance(issuer_ref, str) else "unknown",
            "recipient_name": assertion.get("recipient", {}).get("name", "unknown"),
            "issued_on": assertion.get("issuedOn"),
        },
    }
