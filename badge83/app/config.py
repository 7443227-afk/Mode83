from __future__ import annotations

import os
from pathlib import Path
import re


APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
WORKSPACE_DIR = PROJECT_DIR.parent

DATA_BASE = PROJECT_DIR / "data"
ISSUED_DIR = DATA_BASE / "issued"
BAKED_DIR = DATA_BASE / "baked"
BACKGROUND_IMAGES_DIR = DATA_BASE / "backgrounds"
REGISTRY_DB = DATA_BASE / "registry.db"

ISSUER_TEMPLATE = DATA_BASE / "issuer_template.json"
BADGECLASS_TEMPLATE = DATA_BASE / "badgeclass_template.json"
BADGE_PNG = DATA_BASE / "badge.png"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_PUBLIC_SCHEME = "https"
DEFAULT_PUBLIC_HOST = "mode83.ddns.net"
DEFAULT_PUBLIC_PORT = 443
DEFAULT_BASE_URL = f"{DEFAULT_PUBLIC_SCHEME}://{DEFAULT_PUBLIC_HOST}"
DEFAULT_SEARCH_PEPPER = "badge83-dev-search-pepper"
DEFAULT_AUTH_USERNAME = "admin"
DEFAULT_AUTH_PASSWORD = "admin"
DEFAULT_AUTH_SECRET = "badge83-dev-auth-secret-change-me"
DEFAULT_MAX_PNG_UPLOAD_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_CSV_UPLOAD_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_IMAGE_PIXELS = 50_000_000
DEFAULT_ANCHORING_PROVIDER = "mock"
DEFAULT_EVM_NETWORK_LABEL = "hardhat-local"
DEFAULT_EVM_CONFIRMATION_TIMEOUT_SECONDS = 120
DEFAULT_BLOCKCHAIN_VERIFY_PATH = "/blockchain/verify"
EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
PRODUCTION_ENV_VALUES = {"prod", "production"}

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
    public_port = os.environ.get("BADGE83_PUBLIC_PORT") or str(DEFAULT_PUBLIC_PORT)

    try:
        port_value = int(str(public_port).strip())
    except Exception:
        port_value = DEFAULT_PUBLIC_PORT

    is_standard_port = (public_scheme == "http" and port_value == 80) or (
        public_scheme == "https" and port_value == 443
    )
    if is_standard_port:
        return f"{public_scheme}://{public_host}"
    return f"{public_scheme}://{public_host}:{port_value}"


def get_search_pepper() -> str:
    return os.environ.get("BADGE83_SEARCH_PEPPER", DEFAULT_SEARCH_PEPPER).strip() or DEFAULT_SEARCH_PEPPER


def get_embed_admin_recipient() -> bool:
    """Indique si les données administratives lisibles sont intégrées à l'assertion publique.

    Par défaut, Badge83 applique une minimisation RGPD : l'email complet n'est pas
    inscrit dans l'assertion JSON ni dans le PNG baked. Il reste disponible pour
    l'administration locale via SQLite quand il est fourni au moment de l'émission.
    """
    raw_value = os.environ.get("BADGE83_EMBED_ADMIN_RECIPIENT", "false").strip().lower()
    return raw_value in {"1", "true", "yes", "oui", "on"}


def get_badge83_env() -> str:
    return os.environ.get("BADGE83_ENV", "development").strip().lower() or "development"


def is_production_env() -> bool:
    return get_badge83_env() in PRODUCTION_ENV_VALUES


def get_auth_username() -> str:
    return os.environ.get("BADGE83_AUTH_USERNAME", DEFAULT_AUTH_USERNAME).strip() or DEFAULT_AUTH_USERNAME


def get_auth_password() -> str:
    return os.environ.get("BADGE83_AUTH_PASSWORD", DEFAULT_AUTH_PASSWORD).strip() or DEFAULT_AUTH_PASSWORD


def get_auth_secret() -> str:
    return os.environ.get("BADGE83_AUTH_SECRET", DEFAULT_AUTH_SECRET).strip() or DEFAULT_AUTH_SECRET


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return int(str(raw_value).strip())
    except Exception:
        return default


def get_max_png_upload_bytes() -> int:
    """Taille maximale configurable pour les uploads PNG.

    La valeur par défaut reste volontairement large afin de ne pas bloquer les
    grands PNG métier, comme les attestations ou feuilles de présence hebdomadaires.
    Une valeur <= 0 désactive la limite côté application.
    """
    return _get_int_env("BADGE83_MAX_PNG_UPLOAD_BYTES", DEFAULT_MAX_PNG_UPLOAD_BYTES)


def get_max_csv_upload_bytes() -> int:
    """Taille maximale configurable pour les imports CSV groupés."""
    return _get_int_env("BADGE83_MAX_CSV_UPLOAD_BYTES", DEFAULT_MAX_CSV_UPLOAD_BYTES)


def get_max_image_pixels() -> int:
    """Nombre maximal configurable de pixels pour éviter les decompression bombs."""
    return _get_int_env("BADGE83_MAX_IMAGE_PIXELS", DEFAULT_MAX_IMAGE_PIXELS)


def get_default_anchoring_provider() -> str:
    """Provider d'ancrage utilisé si l'API ne reçoit pas de choix explicite."""
    return os.environ.get("BADGE83_ANCHORING_PROVIDER", DEFAULT_ANCHORING_PROVIDER).strip().lower() or DEFAULT_ANCHORING_PROVIDER


def get_evm_rpc_url() -> str:
    return os.environ.get("BADGE83_EVM_RPC_URL", "").strip()


def get_evm_chain_id() -> int | None:
    raw_value = os.environ.get("BADGE83_EVM_CHAIN_ID", "").strip()
    if not raw_value:
        return None
    try:
        return int(raw_value)
    except Exception:
        return None


def get_evm_contract_address() -> str:
    return os.environ.get("BADGE83_EVM_CONTRACT_ADDRESS", "").strip()


def get_evm_contract_version() -> str:
    """Version du contrat EVM cible: registry par défaut, v2 pour compatibilité historique."""
    return os.environ.get("BADGE83_EVM_CONTRACT_VERSION", "registry").strip().lower() or "registry"


def get_blockchain_verify_base_url() -> str:
    """URL de base du vérificateur blockchain statique indépendant."""
    configured_url = os.environ.get("BADGE83_BLOCKCHAIN_VERIFY_BASE_URL", "").strip().rstrip("/")
    if configured_url:
        return configured_url
    return f"{get_public_base_url().rstrip('/')}{DEFAULT_BLOCKCHAIN_VERIFY_PATH}"


def is_valid_evm_address(address: str) -> bool:
    """Valide le format minimal d'une adresse EVM sans dépendance web3 obligatoire."""
    return bool(EVM_ADDRESS_RE.fullmatch(str(address or "").strip()))


def get_evm_private_key() -> str:
    """Clé privée EVM optionnelle lue depuis l'environnement, jamais loggée."""
    return os.environ.get("BADGE83_EVM_PRIVATE_KEY", "").strip()


def get_evm_network_label() -> str:
    return os.environ.get("BADGE83_EVM_NETWORK_LABEL", DEFAULT_EVM_NETWORK_LABEL).strip() or DEFAULT_EVM_NETWORK_LABEL


def get_evm_explorer_tx_url_template() -> str:
    """Template optionnel d'URL explorer pour afficher un tx_hash public."""
    return os.environ.get("BADGE83_EVM_EXPLORER_TX_URL_TEMPLATE", "").strip()


def get_evm_confirmation_timeout_seconds() -> int:
    timeout = _get_int_env("BADGE83_EVM_CONFIRMATION_TIMEOUT_SECONDS", DEFAULT_EVM_CONFIRMATION_TIMEOUT_SECONDS)
    if timeout <= 0:
        return DEFAULT_EVM_CONFIRMATION_TIMEOUT_SECONDS
    return timeout


def validate_production_security_config() -> None:
    """Refuse les secrets de développement en mode production.

    Le projet peut fonctionner avec des valeurs par défaut en développement local,
    mais une exposition production avec `admin/admin`, un secret de cookie connu ou
    un pepper de recherche par défaut serait dangereuse.
    """
    if not is_production_env():
        return

    if get_auth_password() == DEFAULT_AUTH_PASSWORD:
        raise RuntimeError("BADGE83_AUTH_PASSWORD must be changed in production")
    if get_auth_secret() == DEFAULT_AUTH_SECRET:
        raise RuntimeError("BADGE83_AUTH_SECRET must be changed in production")
    if get_search_pepper() == DEFAULT_SEARCH_PEPPER:
        raise RuntimeError("BADGE83_SEARCH_PEPPER must be changed in production")


def get_registry_db_path() -> Path:
    raw_value = os.environ.get("BADGE83_REGISTRY_DB", str(REGISTRY_DB))
    return Path(raw_value)


def get_preferred_venv_python() -> Path:
    candidates = [
        ROOT_VENV_DIR / "bin" / "python",
        PROJECT_VENV_DIR / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]