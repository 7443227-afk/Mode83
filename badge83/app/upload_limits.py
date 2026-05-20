from __future__ import annotations

from io import BytesIO

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import get_max_image_pixels


async def read_upload_limited(file: UploadFile, max_bytes: int, *, label: str = "Fichier") -> bytes:
    """Lit un UploadFile avec une limite configurable.

    Si `max_bytes <= 0`, la limite applicative est désactivée. Cette possibilité
    existe pour les environnements internes contrôlés, mais elle n'est pas
    recommandée pour une exposition publique.
    """
    if max_bytes <= 0:
        return await file.read()

    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"{label} trop volumineux")
    return content


def ensure_image_pixels_within_limit(content: bytes, *, label: str = "Image") -> None:
    """Vérifie les dimensions d'une image sans la décoder entièrement."""
    max_pixels = get_max_image_pixels()
    if max_pixels <= 0:
        return

    try:
        with Image.open(BytesIO(content)) as image:
            width, height = image.size
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail=f"{label} invalide")

    if width * height > max_pixels:
        raise HTTPException(status_code=413, detail=f"{label} trop grande")