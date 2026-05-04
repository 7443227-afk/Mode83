from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.baker import unbake_badge
from app.routes.badge_constructor import router as badge_constructor_router


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def make_constructor_client(tmp_path, monkeypatch) -> TestClient:
    db_path = tmp_path / "registry.db"
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(db_path))

    app = FastAPI()
    app.include_router(badge_constructor_router)
    return TestClient(app)


def test_update_badge_template_via_api_persists_changes(tmp_path, monkeypatch):
    client = make_constructor_client(tmp_path, monkeypatch)

    schema_response = client.post(
        "/badge-constructor/schemas",
        json={
            "name": "Programme test",
            "description": "Schéma utilisé pour tester la mise à jour d'un modèle.",
            "fields": [
                {
                    "id": "course_name",
                    "label": "Nom du cours",
                    "field_type": "text",
                    "required": True,
                    "position": 1,
                }
            ],
        },
    )
    assert schema_response.status_code == 200
    schema_id = schema_response.json()["id"]

    create_response = client.post(
        "/badge-constructor/templates",
        json={
            "name": "Modèle initial",
            "schema_id": schema_id,
            "text_overlays": [
                {
                    "content_type": "static",
                    "static_text": "MODE83",
                    "position_x": 24,
                    "position_y": 24,
                    "font_size": 24,
                    "font_color": "#0f172a",
                }
            ],
            "qr_code_placement": "bottom-right",
            "qr_code_size": 0.22,
        },
    )
    assert create_response.status_code == 200
    template_id = create_response.json()["id"]

    update_response = client.put(
        f"/badge-constructor/templates/{template_id}",
        json={
            "id": template_id,
            "name": "Modèle modifié",
            "schema_id": schema_id,
            "text_overlays": [
                {
                    "content_type": "field",
                    "field_id": "course_name",
                    "position_x": 80,
                    "position_y": 160,
                    "font_size": 28,
                    "font_color": "#123456",
                }
            ],
            "qr_code_placement": "top-left",
            "qr_code_size": 0.35,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["message"] == "Modèle mis à jour avec succès"

    get_response = client.get(f"/badge-constructor/templates/{template_id}")
    assert get_response.status_code == 200
    updated = get_response.json()

    assert updated["id"] == template_id
    assert updated["name"] == "Modèle modifié"
    assert updated["schema_id"] == schema_id
    assert updated["qr_code_placement"] == "top-left"
    assert updated["qr_code_size"] == 0.35
    assert updated["text_overlays"] == [
        {
            "id": updated["text_overlays"][0]["id"],
            "content_type": "field",
            "static_text": None,
            "field_id": "course_name",
            "font_family": "Arial",
            "font_size": 28,
            "font_color": "#123456",
            "font_style": [],
            "text_align": "left",
            "position_x": 80,
            "position_y": 160,
            "rotation": 0,
            "opacity": 1.0,
            "outline_width": 0,
            "outline_color": "#FFFFFF",
        }
    ]


def test_preview_draft_returns_png_for_static_and_dynamic_overlays(tmp_path, monkeypatch):
    client = make_constructor_client(tmp_path, monkeypatch)

    response = client.post(
        "/badge-constructor/templates/preview-draft",
        json={
            "name": "Aperçu brouillon",
            "text_overlays": [
                {
                    "content_type": "static",
                    "static_text": "MODE83",
                    "position_x": 24,
                    "position_y": 24,
                    "font_size": 24,
                    "font_color": "#0f172a",
                },
                {
                    "content_type": "field",
                    "field_id": "course_name",
                    "position_x": 48,
                    "position_y": 96,
                    "font_size": 20,
                    "font_color": "#123456",
                },
            ],
            "qr_code_placement": "bottom-right",
            "qr_code_size": 0.22,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(PNG_SIGNATURE)


def test_update_unknown_badge_template_returns_404(tmp_path, monkeypatch):
    client = make_constructor_client(tmp_path, monkeypatch)

    response = client.put(
        "/badge-constructor/templates/unknown-template",
        json={
            "name": "Modèle inexistant",
            "text_overlays": [],
            "qr_code_placement": "bottom-right",
            "qr_code_size": 0.22,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Modèle introuvable"


def test_updated_badge_template_can_issue_baked_png(
    tmp_path,
    monkeypatch,
    isolated_issuer_env,
):
    client = make_constructor_client(tmp_path, monkeypatch)

    schema_response = client.post(
        "/badge-constructor/schemas",
        json={
            "name": "Programme émission",
            "fields": [
                {
                    "id": "course_name",
                    "label": "Nom du cours",
                    "field_type": "text",
                    "required": True,
                    "position": 1,
                }
            ],
        },
    )
    assert schema_response.status_code == 200
    schema_id = schema_response.json()["id"]

    create_response = client.post(
        "/badge-constructor/templates",
        json={
            "name": "Modèle à modifier",
            "schema_id": schema_id,
            "text_overlays": [
                {
                    "content_type": "static",
                    "static_text": "Ancien texte",
                    "position_x": 16,
                    "position_y": 16,
                    "font_size": 16,
                    "font_color": "#000000",
                }
            ],
            "qr_code_placement": "bottom-right",
            "qr_code_size": 0.22,
        },
    )
    assert create_response.status_code == 200
    template_id = create_response.json()["id"]

    update_response = client.put(
        f"/badge-constructor/templates/{template_id}",
        json={
            "id": template_id,
            "name": "Modèle émission modifié",
            "schema_id": schema_id,
            "text_overlays": [
                {
                    "content_type": "field",
                    "field_id": "course_name",
                    "position_x": 24,
                    "position_y": 64,
                    "font_size": 20,
                    "font_color": "#123456",
                }
            ],
            "qr_code_placement": "top-left",
            "qr_code_size": 0.2,
        },
    )
    assert update_response.status_code == 200

    issue_response = client.post(
        f"/badge-constructor/templates/{template_id}/issue-baked",
        json={
            "name": "Alice Example",
            "email": "alice@example.com",
            "field_values": {"course_name": "Blockchain Foundations"},
        },
    )

    assert issue_response.status_code == 200
    assert issue_response.headers["content-type"] == "image/png"
    assert issue_response.content.startswith(PNG_SIGNATURE)
    assertion_id = issue_response.headers["X-Badge83-Assertion-Id"]
    assert assertion_id

    assertion = unbake_badge(issue_response.content)
    assert assertion["id"] == f"https://tests.mode83.local/assertions/{assertion_id}"
    assert assertion["badge83_template"] == {
        "id": template_id,
        "name": "Modèle émission modifié",
        "schema_id": schema_id,
    }
    assert assertion["field_values"] == {"course_name": "Blockchain Foundations"}

    saved_assertion = isolated_issuer_env["issued_dir"] / f"{assertion_id}.json"
    saved_png = isolated_issuer_env["baked_dir"] / f"{assertion_id}.png"
    assert saved_assertion.exists()
    assert saved_png.exists()
