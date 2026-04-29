from __future__ import annotations

import sqlite3
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.database import init_db_schema, close_connection
from app.database import (
    add_badge_schema, get_badge_schema_by_id, get_all_badge_schemas,
    update_badge_schema, delete_badge_schema
)
from app.models import BadgeSchema, BadgeField

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


@router.post("/schemas", response_model=dict)
def create_badge_schema(schema: BadgeSchema, db: sqlite3.Connection = Depends(get_db)):
    """Crée un nouveau schéma de badge."""
    try:
        schema_data = _dump_model(schema)
        schema_id = add_badge_schema(db, schema_data)
        return {"id": schema_id, "message": "Schéma créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schemas", response_model=List[dict])
def list_badge_schemas(db: sqlite3.Connection = Depends(get_db)):
    """Liste tous les schémas de badge actifs."""
    try:
        schemas = get_all_badge_schemas(db)
        return schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schemas/{schema_id}", response_model=dict)
def get_badge_schema(schema_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Récupère un schéma de badge par identifiant."""
    try:
        schema = get_badge_schema_by_id(db, schema_id)
        if not schema:
            raise HTTPException(status_code=404, detail="Schéma introuvable")
        return schema
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/schemas/{schema_id}", response_model=dict)
def update_badge_schema_endpoint(schema_id: str, schema: BadgeSchema, db: sqlite3.Connection = Depends(get_db)):
    """Met à jour un schéma de badge existant."""
    try:
        schema_data = _dump_model(schema)
        schema_data["id"] = schema_id
        success = update_badge_schema(db, schema_data)
        if not success:
            raise HTTPException(status_code=404, detail="Schéma introuvable")
        return {"message": "Schéma mis à jour avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/schemas/{schema_id}", response_model=dict)
def delete_badge_schema_endpoint(schema_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Supprime logiquement un schéma de badge."""
    try:
        success = delete_badge_schema(db, schema_id)
        if not success:
            raise HTTPException(status_code=404, detail="Schéma introuvable")
        return {"message": "Schéma supprimé avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schemas/{schema_id}/fields", response_model=dict)
def add_field_to_schema(schema_id: str, field: BadgeField, db: sqlite3.Connection = Depends(get_db)):
    """Ajoute un champ à un schéma existant."""
    try:
        schema = get_badge_schema_by_id(db, schema_id)
        if not schema:
            raise HTTPException(status_code=404, detail="Schéma introuvable")
        
        fields = schema.get("fields", [])
        field_data = _dump_model(field)
        fields.append(field_data)
        
        # Met à jour le schéma avec la nouvelle liste de champs
        schema_data = {
            "id": schema_id,
            "name": schema["name"],
            "description": schema.get("description"),
            "fields": fields,
            "is_active": schema.get("is_active", True),
            "created_at": schema.get("created_at"),
            "updated_at": schema.get("updated_at")
        }
        
        success = update_badge_schema(db, schema_data)
        if not success:
            raise HTTPException(status_code=404, detail="Schéma introuvable")
        
        return {"message": "Champ ajouté au schéma avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/schemas/{schema_id}/fields/{field_id}", response_model=dict)
def remove_field_from_schema(schema_id: str, field_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Retire un champ d'un schéma."""
    try:
        schema = get_badge_schema_by_id(db, schema_id)
        if not schema:
            raise HTTPException(status_code=404, detail="Schéma introuvable")
        
        fields = schema.get("fields", [])
        original_count = len(fields)
        fields = [f for f in fields if f.get("id") != field_id]
        if len(fields) == original_count:
            raise HTTPException(status_code=404, detail="Champ introuvable")
        
        # Met à jour le schéma avec la liste de champs filtrée
        schema_data = {
            "id": schema_id,
            "name": schema["name"],
            "description": schema.get("description"),
            "fields": fields,
            "is_active": schema.get("is_active", True),
            "created_at": schema.get("created_at"),
            "updated_at": schema.get("updated_at")
        }
        
        success = update_badge_schema(db, schema_data)
        if not success:
            raise HTTPException(status_code=404, detail="Schéma introuvable")
        
        return {"message": "Champ retiré du schéma avec succès"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))