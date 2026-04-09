from __future__ import annotations

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.issuer import issue_badge
from app.verifier import verify_badge

app = FastAPI(title="Badge 83")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Affiche la page principale avec les formulaires."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/issue")
async def issue(name: str = Form(...), email: str = Form(...)):
    """Reçoit les informations utilisateur et émet une Assertion Open Badges."""
    badge = issue_badge(name=name, email=email)
    return {"status": "issued", "badge": badge}


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
