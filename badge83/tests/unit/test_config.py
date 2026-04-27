from __future__ import annotations

from app import config


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
