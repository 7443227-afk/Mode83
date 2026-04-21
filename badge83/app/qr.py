from __future__ import annotations

from io import BytesIO

import qrcode
from PIL import Image, ImageOps
from qrcode.constants import ERROR_CORRECT_M


def make_verification_qr_url(base_url: str, assertion_id: str) -> str:
    normalized_base = base_url.rstrip("/")
    return f"{normalized_base}/verify/qr/{assertion_id}"


def overlay_qr_on_badge(png_data: bytes, qr_text: str) -> bytes:
    """Ajoute un QR code visible sur le badge PNG sans toucher au baking metadata.

    Le QR est apposé dans l'angle inférieur droit avec une zone blanche de
    protection afin d'améliorer la lisibilité sur mobile et à l'impression.
    """
    with Image.open(BytesIO(png_data)) as source_image:
        badge = source_image.convert("RGBA")

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    width, height = badge.size
    qr_target_size = max(96, int(min(width, height) * 0.22))
    qr_image = qr_image.resize((qr_target_size, qr_target_size), Image.Resampling.LANCZOS)

    quiet_zone = max(8, qr_target_size // 14)
    qr_panel = ImageOps.expand(qr_image, border=quiet_zone, fill="white")

    panel_width, panel_height = qr_panel.size
    margin = max(12, int(min(width, height) * 0.04))
    pos_x = max(0, width - panel_width - margin)
    pos_y = max(0, height - panel_height - margin)

    composed = badge.copy()
    composed.alpha_composite(qr_panel, (pos_x, pos_y))

    output = BytesIO()
    composed.save(output, format="PNG")
    return output.getvalue()