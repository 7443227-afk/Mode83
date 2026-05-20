from __future__ import annotations

from app import config
import pytest


def test_explicit_base_url_wins_over_internal_port(monkeypatch):
    monkeypatch.setenv("BADGE83_BASE_URL", "https://mode83.ddns.net/")
    monkeypatch.setenv("BADGE83_PORT", "8000")

    assert config.get_public_base_url() == "https://mode83.ddns.net"


def test_default_public_base_url_uses_https_without_internal_port(monkeypatch):
    monkeypatch.delenv("BADGE83_BASE_URL", raising=False)
    monkeypatch.delenv("BADGE83_PUBLIC_SCHEME", raising=False)
    monkeypatch.delenv("BADGE83_PUBLIC_HOST", raising=False)
    monkeypatch.delenv("BADGE83_PUBLIC_PORT", raising=False)
    monkeypatch.setenv("BADGE83_PORT", "8000")

    assert config.get_public_base_url() == "https://mode83.ddns.net"


def test_standard_https_public_port_is_omitted(monkeypatch):
    monkeypatch.delenv("BADGE83_BASE_URL", raising=False)
    monkeypatch.setenv("BADGE83_PUBLIC_SCHEME", "https")
    monkeypatch.setenv("BADGE83_PUBLIC_HOST", "mode83.ddns.net")
    monkeypatch.setenv("BADGE83_PUBLIC_PORT", "443")
    monkeypatch.setenv("BADGE83_PORT", "8000")

    assert config.get_public_base_url() == "https://mode83.ddns.net"


def test_non_standard_public_port_is_preserved(monkeypatch):
    monkeypatch.delenv("BADGE83_BASE_URL", raising=False)
    monkeypatch.setenv("BADGE83_PUBLIC_SCHEME", "https")
    monkeypatch.setenv("BADGE83_PUBLIC_HOST", "mode83.ddns.net")
    monkeypatch.setenv("BADGE83_PUBLIC_PORT", "8443")

    assert config.get_public_base_url() == "https://mode83.ddns.net:8443"


def test_development_env_allows_default_security_values(monkeypatch):
    monkeypatch.delenv("BADGE83_ENV", raising=False)
    monkeypatch.delenv("BADGE83_AUTH_PASSWORD", raising=False)
    monkeypatch.delenv("BADGE83_AUTH_SECRET", raising=False)
    monkeypatch.delenv("BADGE83_SEARCH_PEPPER", raising=False)

    config.validate_production_security_config()


def test_production_env_rejects_default_auth_password(monkeypatch):
    monkeypatch.setenv("BADGE83_ENV", "production")
    monkeypatch.setenv("BADGE83_AUTH_PASSWORD", config.DEFAULT_AUTH_PASSWORD)
    monkeypatch.setenv("BADGE83_AUTH_SECRET", "strong-test-secret")
    monkeypatch.setenv("BADGE83_SEARCH_PEPPER", "strong-test-pepper")

    with pytest.raises(RuntimeError, match="BADGE83_AUTH_PASSWORD"):
        config.validate_production_security_config()


def test_production_env_rejects_default_auth_secret(monkeypatch):
    monkeypatch.setenv("BADGE83_ENV", "production")
    monkeypatch.setenv("BADGE83_AUTH_PASSWORD", "strong-test-password")
    monkeypatch.setenv("BADGE83_AUTH_SECRET", config.DEFAULT_AUTH_SECRET)
    monkeypatch.setenv("BADGE83_SEARCH_PEPPER", "strong-test-pepper")

    with pytest.raises(RuntimeError, match="BADGE83_AUTH_SECRET"):
        config.validate_production_security_config()


def test_production_env_rejects_default_search_pepper(monkeypatch):
    monkeypatch.setenv("BADGE83_ENV", "production")
    monkeypatch.setenv("BADGE83_AUTH_PASSWORD", "strong-test-password")
    monkeypatch.setenv("BADGE83_AUTH_SECRET", "strong-test-secret")
    monkeypatch.setenv("BADGE83_SEARCH_PEPPER", config.DEFAULT_SEARCH_PEPPER)

    with pytest.raises(RuntimeError, match="BADGE83_SEARCH_PEPPER"):
        config.validate_production_security_config()


def test_production_env_accepts_non_default_security_values(monkeypatch):
    monkeypatch.setenv("BADGE83_ENV", "production")
    monkeypatch.setenv("BADGE83_AUTH_PASSWORD", "strong-test-password")
    monkeypatch.setenv("BADGE83_AUTH_SECRET", "strong-test-secret")
    monkeypatch.setenv("BADGE83_SEARCH_PEPPER", "strong-test-pepper")

    config.validate_production_security_config()


def test_upload_limits_can_be_overridden(monkeypatch):
    monkeypatch.setenv("BADGE83_MAX_PNG_UPLOAD_BYTES", "104857600")
    monkeypatch.setenv("BADGE83_MAX_CSV_UPLOAD_BYTES", "20971520")
    monkeypatch.setenv("BADGE83_MAX_IMAGE_PIXELS", "100000000")

    assert config.get_max_png_upload_bytes() == 104857600
    assert config.get_max_csv_upload_bytes() == 20971520
    assert config.get_max_image_pixels() == 100000000


def test_upload_limits_fallback_to_large_defaults(monkeypatch):
    monkeypatch.delenv("BADGE83_MAX_PNG_UPLOAD_BYTES", raising=False)
    monkeypatch.delenv("BADGE83_MAX_CSV_UPLOAD_BYTES", raising=False)
    monkeypatch.delenv("BADGE83_MAX_IMAGE_PIXELS", raising=False)

    assert config.get_max_png_upload_bytes() == config.DEFAULT_MAX_PNG_UPLOAD_BYTES
    assert config.get_max_csv_upload_bytes() == config.DEFAULT_MAX_CSV_UPLOAD_BYTES
    assert config.get_max_image_pixels() == config.DEFAULT_MAX_IMAGE_PIXELS
