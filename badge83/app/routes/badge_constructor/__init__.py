from __future__ import annotations

from fastapi import APIRouter

from . import schemas, templates

router = APIRouter(prefix="/badge-constructor", tags=["badge-constructor"])
router.include_router(schemas.router)
router.include_router(templates.router)