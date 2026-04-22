from __future__ import annotations

import os
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
WORKSPACE_DIR = PROJECT_DIR.parent

DATA_BASE = PROJECT_DIR / "data"
ISSUED_DIR = DATA_BASE / "issued"
BAKED_DIR = DATA_BASE / "baked"

ISSUER_TEMPLATE = DATA_BASE / "issuer_template.json"
BADGECLASS_TEMPLATE = DATA_BASE / "badgeclass_template.json"
BADGE_PNG = DATA_BASE / "badge.png"

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_PUBLIC_SCHEME = "http"
DEFAULT_PUBLIC_HOST = "mode83.ddns.net"
DEFAULT_BASE_URL = f"{DEFAULT_PUBLIC_SCHEME}://{DEFAULT_PUBLIC_HOST}:{DEFAULT_PORT}"
DEFAULT_SEARCH_PEPPER = "badge83-dev-search-pepper"

ROOT_VENV_DIR = WORKSPACE_DIR / ".venv"
PROJECT_VENV_DIR = PROJECT_DIR / ".venv"


def get_host() -> str:
    return os.environ.get("BADGE83_HOST", DEFAULT_HOST).strip() or DEFAULT_HOST


def get_port() -> int:
    raw_port = os.environ.get("BADGE83_PORT", str(DEFAULT_PORT))
    try:
        return int(str(raw_port).strip())
    except Exception:
        return DEFAULT_PORT


def get_public_base_url() -> str:
    explicit_base_url = os.environ.get("BADGE83_BASE_URL")
    if explicit_base_url:
        return explicit_base_url.rstrip("/")

    public_scheme = os.environ.get("BADGE83_PUBLIC_SCHEME", DEFAULT_PUBLIC_SCHEME).strip() or DEFAULT_PUBLIC_SCHEME
    public_host = os.environ.get("BADGE83_PUBLIC_HOST", DEFAULT_PUBLIC_HOST).strip() or DEFAULT_PUBLIC_HOST
    public_port = os.environ.get("BADGE83_PUBLIC_PORT") or os.environ.get("BADGE83_PORT") or str(DEFAULT_PORT)

    try:
        port_value = int(str(public_port).strip())
    except Exception:
        port_value = DEFAULT_PORT

    is_standard_port = (public_scheme == "http" and port_value == 80) or (
        public_scheme == "https" and port_value == 443
    )
    if is_standard_port:
        return f"{public_scheme}://{public_host}"
    return f"{public_scheme}://{public_host}:{port_value}"


def get_search_pepper() -> str:
    return os.environ.get("BADGE83_SEARCH_PEPPER", DEFAULT_SEARCH_PEPPER)


def get_preferred_venv_python() -> Path:
    candidates = [
        ROOT_VENV_DIR / "bin" / "python",
        PROJECT_VENV_DIR / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]