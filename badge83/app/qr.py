from __future__ import annotations

from io import BytesIO

import qrcode
from PIL import Image, ImageOps, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H


QR_SAFE_MARGIN_PX = 12


def _qr_safe_margin(width: int, height: int, panel_width: int, panel_height: int) -> int:
    """Retourne une marge de sécurité qui garde le QR lisible sans bloquer les petits badges."""
    max_possible_margin = max(0, min((width - panel_width) // 2, (height - panel_height) // 2))
    return min(QR_SAFE_MARGIN_PX, max_possible_margin)


def _clamp_qr_position(
    x: int,
    y: int,
    width: int,
    height: int,
    panel_width: int,
    panel_height: int,
) -> tuple[int, int]:
    """Limite la position du QR dans une zone sûre, avec marge par défaut."""
    safe_margin = _qr_safe_margin(width, height, panel_width, panel_height)
    min_x = safe_margin
    min_y = safe_margin
    max_x = max(min_x, width - panel_width - safe_margin)
    max_y = max(min_y, height - panel_height - safe_margin)
    return min(max(x, min_x), max_x), min(max(y, min_y), max_y)


def make_verification_qr_url(base_url: str, assertion_id: str) -> str:
    normalized_base = base_url.rstrip("/")
    return f"{normalized_base}/verify/qr/{assertion_id}"


def overlay_qr_on_badge(
    png_data: bytes, 
    qr_text: str,
    placement: str = "bottom-right",
    size_ratio: float = 0.22,
    offset_x: int = 0,
    offset_y: int = 0,
    foreground_color: str = "#000000",
    background_color: str = "#FFFFFF",
    error_correction: str = "M",
    border: int = 2
) -> bytes:
    """Ajoute un QR code visible sur le badge PNG avec paramètres configurables.

    Args:
        png_data: Données PNG du badge
        qr_text: Texte à encoder dans le QR code
        placement: Position du QR code ("top-left", "top-right", "bottom-left", 
                  "bottom-right", "center", "custom")
        size_ratio: Taille du QR code relatif à la plus petite dimension du badge (0.0-1.0)
        offset_x: Décalage horizontal en pixels depuis la position de base
        offset_y: Décalage vertical en pixels depuis la position de base
        foreground_color: Couleur du premier plan du QR code (hex)
        background_color: Couleur d'arrière-plan du QR code (hex)
        error_correction: Niveau de correction d'erreur ("L", "M", "Q", "H")
        border: Largeur de la bordure du QR code en modules
    
    Returns:
        Données PNG modifiées avec le QR code superposé
    """
    # Associe le niveau de correction d'erreur à la constante qrcode
    error_correction_map = {
        "L": ERROR_CORRECT_L,
        "M": ERROR_CORRECT_M,
        "Q": ERROR_CORRECT_Q,
        "H": ERROR_CORRECT_H
    }
    
    ec_level = error_correction_map.get(error_correction, ERROR_CORRECT_M)
    
    with Image.open(BytesIO(png_data)) as source_image:
        badge = source_image.convert("RGBA")

    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_level,
        box_size=10,
        border=border,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color=foreground_color, back_color=background_color).convert("RGBA")

    width, height = badge.size
    qr_target_size = max(96, int(min(width, height) * size_ratio))
    qr_image = qr_image.resize((qr_target_size, qr_target_size), Image.Resampling.LANCZOS)

    quiet_zone = max(8, qr_target_size // 14)
    qr_panel = ImageOps.expand(qr_image, border=quiet_zone, fill="white")

    panel_width, panel_height = qr_panel.size
    
    # Calcule la position de base selon le placement demandé
    if placement == "top-left":
        base_x, base_y = 0, 0
    elif placement == "top-right":
        base_x, base_y = width - panel_width, 0
    elif placement == "bottom-left":
        base_x, base_y = 0, height - panel_height
    elif placement == "bottom-right":
        base_x, base_y = width - panel_width, height - panel_height
    elif placement == "center":
        base_x, base_y = (width - panel_width) // 2, (height - panel_height) // 2
    elif placement == "custom":
        base_x, base_y = 0, 0
    else:
        # Par défaut : en bas à droite
        base_x, base_y = width - panel_width, height - panel_height
    
    # Applique les décalages et garde le QR dans une zone lisible.
    # La marge de sécurité évite un placement accidentel trop proche des bords.
    pos_x, pos_y = _clamp_qr_position(
        base_x + offset_x,
        base_y + offset_y,
        width,
        height,
        panel_width,
        panel_height,
    )

    composed = badge.copy()
    composed.alpha_composite(qr_panel, (pos_x, pos_y))

    output = BytesIO()
    composed.save(output, format="PNG")
    return output.getvalue()


def overlay_text_on_badge(
    png_data: bytes,
    text_overlays: list[dict],
    field_values: dict | None = None,
    default_font_size: int = 16
) -> bytes:
    """Ajoute des éléments de texte sur le badge PNG.

    Args:
        png_data: Données PNG du badge
        text_overlays: Liste de configurations de texte overlay
        default_font_size: Taille de police par défaut si non spécifiée
    
    Returns:
        Données PNG modifiées avec le texte superposé
    """
    with Image.open(BytesIO(png_data)) as source_image:
        badge = source_image.convert("RGBA")
    
    # Crée le contexte de dessin
    draw = ImageDraw.Draw(badge)
    
    width, height = badge.size
    
    field_values = field_values or {}

    for overlay in text_overlays:
        # Détermine le contenu du texte
        if overlay.get("content_type") == "static":
            text = overlay.get("static_text", "")
        elif overlay.get("content_type") == "field":
            field_id = overlay.get("field_id")
            text = str(field_values.get(field_id) or f"[{field_id}]")
        else:
            continue
            
        if not text:
            continue
            
        # Propriétés du texte
        font_family = overlay.get("font_family", "Arial")
        font_size = overlay.get("font_size", default_font_size)
        font_color = overlay.get("font_color", "#000000")
        font_style_list = overlay.get("font_style", [])
        text_align = overlay.get("text_align", "left")
        position_x = overlay.get("position_x", 0)
        position_y = overlay.get("position_y", 0)
        rotation = overlay.get("rotation", 0)
        opacity = overlay.get("opacity", 1.0)
        outline_width = overlay.get("outline_width", 0)
        outline_color = overlay.get("outline_color", "#FFFFFF")
        
        # Tente de charger la police, puis utilise une police par défaut si nécessaire
        try:
            # Tente de charger une police TrueType
            font = ImageFont.truetype(f"{font_family}.ttf", font_size)
        except OSError:
            try:
                # Tente les chemins de polices courants
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except OSError:
                # Repli sur la police par défaut
                font = ImageFont.load_default()
        
        # Les styles gras/italique nécessiteraient des variantes de police dédiées
        
        # Calcule la position du texte
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Applique l'alignement du texte
        if text_align == "center":
            adjusted_x = position_x - text_width // 2
        elif text_align == "right":
            adjusted_x = position_x - text_width
        else:  # left
            adjusted_x = position_x
            
        adjusted_y = position_y
        
        # Maintient le texte dans les limites du badge
        adjusted_x = max(0, min(adjusted_x, width - text_width))
        adjusted_y = max(0, min(adjusted_y, height - text_height))
        
        # Crée une couche temporaire pour gérer rotation, opacité et contour
        if rotation != 0 or opacity < 1.0 or outline_width > 0:
            # Crée une couche transparente pour le texte
            text_layer = Image.new("RGBA", badge.size, (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_layer)
            
            # Dessine le contour si demandé
            if outline_width > 0:
                # Dessine le texte plusieurs fois pour créer l'effet de contour
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx == 0 and dy == 0:
                            continue  # Ignore le pixel central
                        text_draw.text(
                            (adjusted_x + dx, adjusted_y + dy), 
                            text, 
                            font=font, 
                            fill=outline_color
                        )
            
            # Dessine le texte principal
            text_draw.text(
                (adjusted_x, adjusted_y), 
                text, 
                font=font, 
                fill=font_color
            )
            
            # Applique la rotation
            if rotation != 0:
                # Rotation autour du centre du texte
                text_layer = text_layer.rotate(
                    rotation, 
                    resample=Image.BICUBIC, 
                    expand=False,
                    center=(adjusted_x + text_width//2, adjusted_y + text_height//2)
                )
            
            # Applique l'opacité
            if opacity < 1.0:
                alpha = text_layer.split()[3]
                alpha = Image.eval(alpha, lambda a: int(a * opacity))
                text_layer.putalpha(alpha)
            
            # Fusionne la couche de texte sur le badge
            badge = Image.alpha_composite(badge, text_layer)
        else:
            # Cas simple : sans rotation, opacité complète, pas de couche dédiée
            # Dessine le contour si demandé
            if outline_width > 0:
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text(
                            (adjusted_x + dx, adjusted_y + dy), 
                            text, 
                            font=font, 
                            fill=outline_color
                        )
            
            # Dessine le texte principal
            draw.text(
                (adjusted_x, adjusted_y), 
                text, 
                font=font, 
                fill=font_color
            )
    
    output = BytesIO()
    badge.save(output, format="PNG")
    return output.getvalue()