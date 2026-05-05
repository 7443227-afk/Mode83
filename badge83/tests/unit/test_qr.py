from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageChops

from app.qr import overlay_qr_on_badge


def _make_plain_png(size: tuple[int, int] = (400, 300), color=(255, 255, 255, 255)) -> bytes:
    image = Image.new("RGBA", size, color=color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _rgb_difference_bbox(left: Image.Image, right: Image.Image):
    return ImageChops.difference(left.convert("RGB"), right.convert("RGB")).getbbox()


def test_overlay_qr_on_badge_custom_position_returns_modified_png():
    source_png = _make_plain_png()

    result_png = overlay_qr_on_badge(
        source_png,
        "https://tests.mode83.local/verify/qr/custom-position",
        placement="custom",
        size_ratio=0.22,
        offset_x=40,
        offset_y=50,
    )

    with Image.open(BytesIO(source_png)) as source_image, Image.open(BytesIO(result_png)) as result_image:
        source = source_image.convert("RGBA")
        result = result_image.convert("RGBA")

    assert result.size == source.size
    assert result.format is None  # converted image, loaded successfully from a PNG payload
    assert _rgb_difference_bbox(source, result) is not None

    expected_qr_area = result.crop((40, 50, 180, 190))
    assert _rgb_difference_bbox(
        Image.new("RGBA", expected_qr_area.size, (255, 255, 255, 255)), expected_qr_area
    ) is not None


def test_overlay_qr_on_badge_custom_position_is_clamped_to_badge_bounds():
    source_png = _make_plain_png(size=(220, 180))

    result_png = overlay_qr_on_badge(
        source_png,
        "https://tests.mode83.local/verify/qr/clamped-position",
        placement="custom",
        size_ratio=0.5,
        offset_x=10_000,
        offset_y=10_000,
    )

    with Image.open(BytesIO(result_png)) as result_image:
        result = result_image.convert("RGBA")

    assert result.size == (220, 180)
    bottom_right_area = result.crop((120, 80, 220, 180))
    assert _rgb_difference_bbox(
        Image.new("RGBA", bottom_right_area.size, (255, 255, 255, 255)), bottom_right_area
    ) is not None