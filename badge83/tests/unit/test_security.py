from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.baker import bake_badge_from_bytes
from app.main import app
from app.security import SSRFProtectionError, validate_public_http_url
from app.verifier import deep_verify_baked_badge


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/assertions/1",
        "http://127.0.0.1/assertions/1",
        "http://10.0.0.12/assertions/1",
        "http://172.16.0.5/assertions/1",
        "http://192.168.1.10/assertions/1",
        "http://[::1]/assertions/1",
        "http://[fe80::1]/assertions/1",
    ],
)
def test_validate_public_http_url_refuse_les_cibles_locales(url):
    with pytest.raises(SSRFProtectionError):
        validate_public_http_url(url)


def test_validate_public_http_url_refuse_dns_vers_adresse_privee(monkeypatch):
    def fake_getaddrinfo(*args, **kwargs):
        return [(None, None, None, None, ("127.0.0.1", 443))]

    monkeypatch.setattr("socket.getaddrinfo", fake_getaddrinfo)

    with pytest.raises(SSRFProtectionError, match="adresse non publique"):
        validate_public_http_url("https://issuer.example.org/assertions/1")


def test_validate_public_http_url_accepte_dns_public(monkeypatch):
    def fake_getaddrinfo(*args, **kwargs):
        return [(None, None, None, None, ("93.184.216.34", 443))]

    monkeypatch.setattr("socket.getaddrinfo", fake_getaddrinfo)

    assert validate_public_http_url("https://issuer.example.org/assertions/1") == "https://issuer.example.org/assertions/1"


def test_deep_verify_baked_badge_refuse_ssrf_sans_exposer_exception(sample_png_bytes):
    assertion = {
        "id": "http://127.0.0.1:8000/assertions/private",
        "type": "Assertion",
        "badge": "https://tests.mode83.local/badges/blockchain-foundations",
        "issuer": "https://tests.mode83.local/issuers/main",
        "issuedOn": "2026-05-28T10:00:00+00:00",
        "recipient": {
            "type": "email",
            "hashed": True,
            "salt": "abc",
            "identity": "sha256$" + "a" * 64,
        },
        "verification": {"type": "HostedBadge", "url": "http://127.0.0.1:8000/assertions/private"},
    }
    baked = bake_badge_from_bytes(sample_png_bytes, assertion)

    result = deep_verify_baked_badge(baked)

    assert result["deep"]["ok"] is False
    assert result["deep"]["hosted_assertion"]["ok"] is False
    assert "refus" in result["deep"]["hosted_assertion"]["error"].lower()


def test_verify_online_refuse_url_locale():
    client = TestClient(app)

    response = client.post("/verify-online", data={"assertion_url": "http://127.0.0.1:8000/assertions/private"})

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["error"] == "Impossible de récupérer une assertion valide depuis cette URL"


def test_public_assets_refuse_path_traversal():
    client = TestClient(app)

    response = client.get("/assets/..%2Fbadge83.env")

    assert response.status_code == 404


def test_admin_routes_rejettent_upload_trop_gros(monkeypatch, sample_png_bytes):
    monkeypatch.setenv("BADGE83_MAX_PNG_UPLOAD_BYTES", "10")
    client = TestClient(app)

    response = client.post(
        "/verify-baked",
        files={"badge": ("badge.png", sample_png_bytes, "image/png")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "PNG trop volumineux"