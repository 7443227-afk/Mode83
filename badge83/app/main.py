from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.templating import Jinja2Templates

from app.issuer import issue_badge, issue_baked_badge
from app.verifier import verify_badge, verify_baked_badge

app = FastAPI(title="Badge 83")
templates = Jinja2Templates(directory="templates")
DATA_BASE = Path(__file__).resolve().parent.parent / "data"


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Affiche la page principale avec les formulaires."""
    return templates.TemplateResponse("index.html", {"request": request})


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
