from __future__ import annotations

import sqlite3
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Body
from fastapi.responses import Response
from typing import List
import base64

from app.config import BADGE_PNG
from app.database import init_db_schema, close_connection
from app.database import (
    add_badge_template, get_badge_template_by_id, get_all_badge_templates,
    update_badge_template, delete_badge_template, get_badge_schema_by_id
)
from app.issuer import issue_baked_badge_from_template
from app.models import BadgeTemplate, TextOverlay
from app.qr import overlay_qr_on_badge, overlay_text_on_badge

router = APIRouter()


def get_db():
    """Dépendance FastAPI fournissant une connexion à la base de données."""
    conn = init_db_schema()
    try:
        yield conn
    finally:
        close_connection(conn)


def _dump_model(model):
    """Conversion en dictionnaire compatible Pydantic v2/v1."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _template_update_payload(template_id: str, template: dict, **overrides) -> dict:
    """Construit une charge complète en conservant les valeurs actuelles et les surcharges."""
    payload = {
        "id": template_id,
        "name": template["name"],
        "description": template.get("description"),
        "schema_id": template.get("schema_id"),
        "background_image": template.get("background_image"),
        "text_overlays": template.get("text_overlays", []),
        "qr_code_placement": template.get("qr_code_placement", "bottom-right"),
        "qr_code_size": template.get("qr_code_size", 0.22),
        "qr_code_offset_x": template.get("qr_code_offset_x", 0),
        "qr_code_offset_y": template.get("qr_code_offset_y", 0),
        "qr_code_foreground_color": template.get("qr_code_foreground_color", "#000000"),
        "qr_code_background_color": template.get("qr_code_background_color", "#FFFFFF"),
        "qr_code_error_correction": template.get("qr_code_error_correction", "M"),
        "qr_code_border": template.get("qr_code_border", 2),
        "is_active": template.get("is_active", True),
        "created_at": template.get("created_at"),
    }
    payload.update(overrides)
    return payload


def _load_template_background(template: dict) -> bytes:
    """Retourne le PNG de fond du modèle, ou l'image de badge par défaut."""
    background_image = template.get("background_image")
    if isinstance(background_image, str) and background_image.startswith("data:") and ";base64," in background_image:
        _, encoded = background_image.split(";base64,", 1)
        return base64.b64decode(encoded)
    if isinstance(background_image, str) and background_image.strip():
        try:
            return BADGE_PNG.parent.joinpath(background_image).read_bytes()
        except Exception:
            pass
    return BADGE_PNG.read_bytes()


@router.post("/templates", response_model=dict)
def create_badge_template(template: BadgeTemplate, db: sqlite3.Connection = Depends(get_db)):
    """Crée un nouveau modèle de badge."""
    try:
        template_data = _dump_model(template)
        template_id = add_badge_template(db, template_data)
        return {"id": template_id, "message": "Modèle créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=List[dict])
def list_badge_templates(db: sqlite3.Connection = Depends(get_db)):
    """Liste tous les modèles de badge actifs."""
    try:
        templates = get_all_badge_templates(db)
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", response_model=dict)
def get_badge_template(template_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Récupère un modèle de badge par identifiant."""
    try:
        template = get_badge_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Modèle introuvable")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}/preview", response_class=Response)
def preview_badge_template(template_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Génère un aperçu PNG avec textes superposés et placement du QR code configurés."""
    try:
        template = get_badge_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Modèle introuvable")

        png_data = _load_template_background(template)
        png_data = overlay_text_on_badge(png_data, template.get("text_overlays", []))
        png_data = overlay_qr_on_badge(
            png_data,
            "https://mode83.example/verify/qr/preview",
            placement=template.get("qr_code_placement", "bottom-right"),
            size_ratio=float(template.get("qr_code_size", 0.22)),
            offset_x=int(template.get("qr_code_offset_x", 0)),
            offset_y=int(template.get("qr_code_offset_y", 0)),
            foreground_color=template.get("qr_code_foreground_color", "#000000"),
            background_color=template.get("qr_code_background_color", "#FFFFFF"),
            error_correction=template.get("qr_code_error_correction", "M"),
            border=int(template.get("qr_code_border", 2)),
        )
        return Response(content=png_data, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/templates/preview-draft", response_class=Response)
def preview_badge_template_draft(payload: dict = Body(...)):
    """Génère un aperçu PNG avant l'enregistrement d'un modèle."""
    try:
        template = dict(payload or {})
        png_data = _load_template_background(template)
        sample_values = {
            "name": "Alice Example",
            "recipient_name": "Alice Example",
            "email": "alice@example.org",
            "recipient_email": "alice@example.org",
            "course_name": "Blockchain Foundations",
            "certificate_number": "BF-2026-001",
            "issue_date": "2026-04-29",
        }
        png_data = overlay_text_on_badge(
            png_data,
            template.get("text_overlays", []),
            field_values=sample_values,
        )
        png_data = overlay_qr_on_badge(
            png_data,
            "https://mode83.example/verify/qr/preview",
            placement=template.get("qr_code_placement", "bottom-right"),
            size_ratio=float(template.get("qr_code_size", 0.22)),
            offset_x=int(template.get("qr_code_offset_x", 0)),
            offset_y=int(template.get("qr_code_offset_y", 0)),
            foreground_color=template.get("qr_code_foreground_color", "#000000"),
            background_color=template.get("qr_code_background_color", "#FFFFFF"),
            error_correction=template.get("qr_code_error_correction", "M"),
            border=int(template.get("qr_code_border", 2)),
        )
        return Response(content=png_data, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/templates/{template_id}/issue-baked", response_class=Response)
def issue_badge_from_template(
    template_id: str,
    payload: dict = Body(...),
    db: sqlite3.Connection = Depends(get_db),
):
    """Émet un badge baked en utilisant un modèle du constructeur."""
    try:
        template = get_badge_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Modèle introuvable")

        name = str(payload.get("name") or "").strip()
        email = str(payload.get("email") or "").strip()
        field_values = payload.get("field_values") if isinstance(payload.get("field_values"), dict) else {}

        if not name or not email:
            raise HTTPException(status_code=400, detail="Le nom et l'email sont obligatoires")

        schema_id = template.get("schema_id")
        if schema_id:
            schema = get_badge_schema_by_id(db, schema_id)
            for field in (schema or {}).get("fields", []):
                field_id = field.get("id")
                if field.get("required") and field_id and not str(field_values.get(field_id, "")).strip():
                    raise HTTPException(status_code=400, detail=f"Champ obligatoire manquant : {field.get('label') or field_id}")

        png_data = _load_template_background(template)
        result = issue_baked_badge_from_template(
            name=name,
            email=email,
            template=template,
            field_values=field_values,
            png_data=png_data,
        )
        return Response(
            content=result["baked_png_bytes"],
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="{result.get("baked_download_filename", f"badge-{result["assertion_id"]}.png")}"',
                "X-Badge83-Assertion-Id": result["assertion_id"],
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/templates/{template_id}", response_model=dict)
def update_badge_template_endpoint(template_id: str, template: BadgeTemplate, db: sqlite3.Connection = Depends(get_db)):
    """Met à jour un modèle de badge existant."""
    try:
        template_data = _dump_model(template)
        template_data["id"] = template_id
        success = update_badge_template(db, template_data)
        if not success:
            raise HTTPException(status_code=404, detail="Modèle introuvable")
        return {"message": "Modèle mis à jour avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/templates/{template_id}", response_model=dict)
def delete_badge_template_endpoint(template_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Supprime logiquement un modèle de badge."""
    try:
        success = delete_badge_template(db, template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Modèle introuvable")
        return {"message": "Modèle supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_id}/duplicate", response_model=dict)
def duplicate_badge_template(template_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Duplique un modèle pour créer rapidement une variante de programme."""
    try:
        template = get_badge_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Modèle introuvable")

        duplicated = dict(template)
        duplicated["id"] = str(uuid4())
        duplicated["name"] = f"Copie de {template.get('name', 'modèle')}"
        duplicated["created_at"] = None
        duplicated["updated_at"] = None
        duplicated["is_active"] = True
        new_id = add_badge_template(db, duplicated)
        return {"id": new_id, "message": "Modèle dupliqué avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/templates/{template_id}/background-image", response_model=dict)
async def upload_background_image(template_id: str, file: UploadFile = File(...), db: sqlite3.Connection = Depends(get_db)):
    """Téléverse une image de fond pour un modèle de badge."""
    try:
        template = get_badge_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Modèle introuvable")
        
        # Lit et encode l'image en base64
        content = await file.read()
        base64_image = base64.b64encode(content).decode('utf-8')
        
        template_data = _template_update_payload(
            template_id,
            template,
            background_image=f"data:{file.content_type or 'image/png'};base64,{base64_image}",
        )
        
        success = update_badge_template(db, template_data)
        if not success:
            raise HTTPException(status_code=404, detail="Modèle introuvable")
        
        return {"message": "Image de fond téléversée avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/templates/{template_id}/text-overlays", response_model=dict)
def add_text_overlay(template_id: str, overlay: TextOverlay, db: sqlite3.Connection = Depends(get_db)):
    """Ajoute un texte superposé à un modèle de badge."""
    try:
        template = get_badge_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Modèle introuvable")
        
        overlays = template.get("text_overlays", [])
        overlay_data = _dump_model(overlay)
        overlays.append(overlay_data)
        
        template_data = _template_update_payload(template_id, template, text_overlays=overlays)
        
        success = update_badge_template(db, template_data)
        if not success:
            raise HTTPException(status_code=404, detail="Modèle introuvable")
        
        return {"id": overlay_data["id"], "message": "Texte superposé ajouté avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/templates/{template_id}/text-overlays/{overlay_id}", response_model=dict)
def remove_text_overlay(template_id: str, overlay_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Retire un texte superposé d'un modèle de badge."""
    try:
        template = get_badge_template_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Modèle introuvable")
        
        overlays = template.get("text_overlays", [])
        original_count = len(overlays)
        overlays = [o for o in overlays if o.get("id") != overlay_id]
        if len(overlays) == original_count:
            raise HTTPException(status_code=404, detail="Texte superposé introuvable")
        
        template_data = _template_update_payload(template_id, template, text_overlays=overlays)
        
        success = update_badge_template(db, template_data)
        if not success:
            raise HTTPException(status_code=404, detail="Modèle introuvable")
        
        return {"message": "Texte superposé retiré avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))