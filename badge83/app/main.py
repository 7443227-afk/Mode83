from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx

from fastapi import Depends, FastAPI, Form, Request, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import BAKED_DIR, DATA_BASE, ISSUED_DIR, get_auth_password, get_auth_secret, get_auth_username, get_default_anchoring_provider, get_evm_explorer_tx_url_template, get_max_png_upload_bytes, get_public_base_url, validate_production_security_config
from app.database import delete_assertion_record, import_assertions_from_directory, sync_assertion_record
from app.issuer import issue_badge, issue_baked_badge, normalize_email, normalize_name, make_search_hash, enregistrer_evenement_audit
from app.openbadges_checks import check_assertion
from app.proofs import HashService
from app.proofs.anchoring_repository import AnchoringRepository
from app.proofs.anchoring_service import AnchoringService
from app.proofs.anchoring_providers import EvmAnchoringProvider, get_anchoring_provider
from app.proofs.audit_repository import AuditRepository
from app.proofs.blockchain_revocation_repository import BlockchainRevocationRepository
from app.proofs.repository import ProofRepository
from app.proofs.revocation_repository import RevocationRepository
from app.security import MAX_REMOTE_JSON_BYTES, MAX_REMOTE_REDIRECTS, SSRFProtectionError, validate_public_http_url
from app.upload_limits import ensure_image_pixels_within_limit, read_upload_limited
from app.verifier import deep_verify_baked_badge, verify_badge, verify_baked_badge
from app.routes.badge_constructor import router as badge_constructor_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production_security_config()
    ISSUED_DIR.mkdir(parents=True, exist_ok=True)
    # Initialise le schéma de base de données du constructeur de badges
    from app.database import init_db_schema

    init_db_schema()
    import_assertions_from_directory(ISSUED_DIR)
    yield


app = FastAPI(title="Badge 83", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


def _compose_public_base_url() -> str:
    return get_public_base_url()


BASE_URL = _compose_public_base_url()
OB_CONTENT_TYPE = 'application/ld+json; charset=utf-8; profile="https://w3id.org/openbadges/v2"'
AUTH_COOKIE_NAME = "badge83_auth"
AUTH_COOKIE_MAX_AGE = 60 * 60 * 8


def _auth_signature(payload: str) -> str:
    digest = hmac.new(get_auth_secret().encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _make_auth_cookie(username: str) -> str:
    issued_at = str(int(time.time()))
    payload = base64.urlsafe_b64encode(f"{username}:{issued_at}".encode("utf-8")).decode("ascii").rstrip("=")
    return f"{payload}.{_auth_signature(payload)}"


def _decode_auth_cookie(cookie_value: str | None) -> str | None:
    if not cookie_value or "." not in cookie_value:
        return None

    payload, signature = cookie_value.rsplit(".", 1)
    if not hmac.compare_digest(signature, _auth_signature(payload)):
        return None

    try:
        padded_payload = payload + "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(padded_payload.encode("ascii")).decode("utf-8")
        username, issued_at_raw = decoded.rsplit(":", 1)
        issued_at = int(issued_at_raw)
    except Exception:
        return None

    if int(time.time()) - issued_at > AUTH_COOKIE_MAX_AGE:
        return None
    return username


def _is_auth_cookie_valid(request: Request) -> bool:
    return _decode_auth_cookie(request.cookies.get(AUTH_COOKIE_NAME)) == get_auth_username()


def require_admin(request: Request) -> None:
    """Protège les routes administrateur même sans reverse proxy Nginx.

    Nginx `auth_request` reste utile comme première barrière, mais les endpoints
    sensibles doivent aussi refuser directement les appels FastAPI non autorisés.
    """
    if not _is_auth_cookie_valid(request):
        raise HTTPException(status_code=401, detail="Authentication required")


app.include_router(badge_constructor_router, dependencies=[Depends(require_admin)])


def _safe_next_url(next_url: str | None) -> str:
    if not next_url or not next_url.startswith("/") or next_url.startswith("//"):
        return "/"
    if next_url.startswith("/auth/"):
        return "/"
    return next_url


# ---------------------------------------------------------------------------
# CORS — autoriser les validateurs externes (ex. validator.openbadges.org) à récupérer les ressources
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
async def index(request: Request):
    """Affiche la nouvelle console d'administration Badge83."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/auth/login", response_class=HTMLResponse)
async def auth_login_page(request: Request, next: str | None = None):
    """Affiche la page de connexion utilisée par Nginx auth_request."""
    next_url = _safe_next_url(next)
    if _is_auth_cookie_valid(request):
        return RedirectResponse(url=next_url, status_code=303)
    return templates.TemplateResponse("auth_login.html", {"request": request, "error": None, "next_url": next_url})


@app.post("/auth/login")
async def auth_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next_url: str = Form("/"),
):
    """Valide les identifiants et pose la session cookie vérifiée par Nginx."""
    target_url = _safe_next_url(next_url)
    credentials_ok = secrets.compare_digest(username, get_auth_username()) and secrets.compare_digest(
        password,
        get_auth_password(),
    )
    if not credentials_ok:
        return templates.TemplateResponse(
            "auth_login.html",
            {"request": request, "error": "Identifiant ou mot de passe incorrect", "next_url": target_url},
            status_code=401,
        )

    response = RedirectResponse(url=target_url, status_code=303)
    response.set_cookie(
        AUTH_COOKIE_NAME,
        _make_auth_cookie(username),
        max_age=AUTH_COOKIE_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return response


@app.get("/auth/check")
async def auth_check(request: Request):
    """Endpoint interne pour Nginx auth_request : 204 si autorisé, 401 sinon."""
    if _is_auth_cookie_valid(request):
        return Response(status_code=204)
    return Response(status_code=401)


@app.get("/auth/logout")
async def auth_logout():
    """Supprime la cookie de session et renvoie vers la page de connexion."""
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie(AUTH_COOKIE_NAME)
    return response


@app.get("/verify/badge/{assertion_id}", response_class=HTMLResponse)
async def verify_badge_page(request: Request, assertion_id: str):
    """Affiche une page de vérification lisible par un humain pour un badge donné."""
    record = _collect_badge_record(assertion_id)
    not_found = record is None

    if not_found:
        context = {
            "request": request,
            "assertion_id": assertion_id,
            "not_found": True,
            "status": "not_found",
            "status_label": "Badge introuvable",
            "status_tone": "warning",
            "badge": None,
        }
        return templates.TemplateResponse("verify_badge.html", context, status_code=404)

    public_assertion_url = record.get("public_assertion_url")
    status = "valid" if record.get("has_json") else "partial"
    status_label = "Badge valide" if status == "valid" else "Enregistrement incomplet"
    status_tone = "success" if status == "valid" else "secondary"

    context = {
        "request": request,
        "assertion_id": assertion_id,
        "not_found": False,
        "status": status,
        "status_label": status_label,
        "status_tone": status_tone,
        "badge": {
            **record,
            "verification_page_url": str(request.url),
            "raw_assertion_url": public_assertion_url,
        },
    }
    return templates.TemplateResponse("verify_badge.html", context)


@app.get("/verify/qr/{assertion_id}", response_class=HTMLResponse)
async def verify_badge_qr_page(request: Request, assertion_id: str):
    """Affiche une page mobile minimale pour une vérification par QR."""
    record = _collect_badge_record(assertion_id)

    if record is None:
        context = {
            "request": request,
            "assertion_id": assertion_id,
            "not_found": True,
            "hero_tone": "bad",
            "status_icon": "✕",
            "status_title": "Badge introuvable",
            "status_message": "Aucune preuve locale n’a été trouvée pour cet identifiant.",
            "badge": None,
        }
        return templates.TemplateResponse("verify_qr.html", context, status_code=404)

    issuer_check = _build_issuer_check(record.get("assertion") or {})
    admin_recipient = (
        record.get("assertion", {}).get("admin_recipient", {})
        if isinstance(record.get("assertion"), dict)
        else {}
    )
    is_valid = bool(record.get("has_json"))
    is_mode83 = bool(issuer_check.get("is_local"))

    if is_valid and is_mode83:
        hero_tone = "ok"
        status_icon = "✓"
        status_title = "Badge vérifié"
        status_message = "Badge valide et émis par MODE83."
    elif is_valid:
        hero_tone = "warn"
        status_icon = "!"
        status_title = "Badge valide"
        status_message = "Badge valide, mais émis par un autre organisme."
    else:
        hero_tone = "bad"
        status_icon = "✕"
        status_title = "Vérification incomplète"
        status_message = "Les preuves attendues sont incomplètes pour ce badge."

    context = {
        "request": request,
        "assertion_id": assertion_id,
        "not_found": False,
        "hero_tone": hero_tone,
        "status_icon": status_icon,
        "status_title": status_title,
        "status_message": status_message,
        "badge": {
            **record,
            "is_valid": is_valid,
            "is_mode83": is_mode83,
            "issuer_label": issuer_check.get("label") or record.get("issuer_name"),
            "issued_on_display": _format_display_date(record.get("issued_on")),
            "recipient_name": admin_recipient.get("name") or "Non disponible",
            "recipient_email": _mask_email(admin_recipient.get("email")),
            "full_verification_url": f"/verify/badge/{assertion_id}" if is_valid and is_mode83 else None,
        },
    }
    return templates.TemplateResponse("verify_qr.html", context)


@app.get("/verify-desk", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
async def verify_desk_page(request: Request):
    """Affiche une page de vérification simplifiée pour un usage secrétariat."""
    return templates.TemplateResponse("verify_desk.html", {"request": request})


@app.get("/legacy", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
async def legacy_index(request: Request):
    """Affiche l'ancienne interface pour rollback rapide."""
    return templates.TemplateResponse("index_legacy.html", {"request": request})


@app.get("/badge.png")
async def get_badge_png():
    """Télécharge l'image badge par défaut (pour baking local ou référence)."""
    return FileResponse(DATA_BASE / "badge.png", media_type="image/png")


@app.post("/issue", dependencies=[Depends(require_admin)])
async def issue(name: str = Form(...), email: str = Form(...)):
    """Reçoit les informations utilisateur et émet une Assertion Open Badges."""
    badge = issue_badge(name=name, email=email)
    return {"status": "issued", "badge": badge}


@app.post("/issue-baked", dependencies=[Depends(require_admin)])
async def issue_baked(name: str = Form(...), email: str = Form(...), badge_image: UploadFile | None = File(None)):
    """Émet un badge Open Badges baked dans un PNG.

    Si *badge_image* est fourni (upload), il est utilisé comme base.
    Sinon le PNG par défaut ``data/badge.png`` est utilisé.
    """
    png_data = None
    if badge_image:
        png_data = await read_upload_limited(badge_image, get_max_png_upload_bytes(), label="PNG")
        ensure_image_pixels_within_limit(png_data, label="PNG")
    result = issue_baked_badge(name=name, email=email, png_data=png_data)
    return Response(
        content=result["baked_png_bytes"],
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{result.get("baked_download_filename", f"badge-{result["assertion_id"]}.png")}"',
            "X-Badge83-Assertion-Id": result["assertion_id"],
        },
    )


@app.get("/verify/{badge_id}")
async def verify(badge_id: str):
    """Vérifie l'existence d'une Assertion Open Badges via son identifiant."""
    result = verify_badge(badge_id=badge_id)
    return result


@app.get("/verify")
async def verify_query(badge_id: str):
    """Permet la vérification via query string (?badge_id=...)."""
    result = verify_badge(badge_id=badge_id)
    return result


@app.post("/verify-baked")
async def verify_baked(badge: UploadFile = File(...), deep: bool = False):
    """Vérifie un badge Open Badges à partir d'un PNG baked uploadé."""
    png_data = await read_upload_limited(badge, get_max_png_upload_bytes(), label="PNG")
    ensure_image_pixels_within_limit(png_data, label="PNG")
    result = deep_verify_baked_badge(png_data) if deep else verify_baked_badge(png_data)
    return result


def _extract_assertion_id(assertion: dict[str, Any]) -> str:
    assertion_id = assertion.get("id", "")
    if isinstance(assertion_id, str) and "/" in assertion_id:
        return assertion_id.rstrip("/").split("/")[-1]
    return str(assertion_id or "unknown")


def _safe_load_json(file_path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _is_probable_email(query: str) -> bool:
    return "@" in query and "." in query.split("@")[-1]


def _matches_email_query(assertion: dict[str, Any], query: str) -> bool:
    recipient = assertion.get("recipient", {}) if isinstance(assertion.get("recipient"), dict) else {}
    salt = recipient.get("salt")
    identity = recipient.get("identity")
    if not salt or not identity:
        return False

    expected_hash = "sha256$" + __import__("hashlib").sha256(
        normalize_email(query).encode("utf-8") + str(salt).encode("utf-8")
    ).hexdigest()
    return expected_hash == identity


def _matches_search_query(record: dict[str, Any], query: str) -> bool:
    normalized_query = query.strip()
    if not normalized_query:
        return True

    assertion = record.get("assertion", {}) if isinstance(record.get("assertion"), dict) else {}
    search_data = assertion.get("search", {}) if isinstance(assertion.get("search"), dict) else {}
    lowered_query = normalized_query.lower()

    searchable_text = " ".join(
        [
            str(record.get("assertion_id", "")),
            str(record.get("badge_name", "")),
            str(record.get("issuer_name", "")),
            str(record.get("recipient", {}).get("identity", "")),
        ]
    ).lower()
    if lowered_query in searchable_text:
        return True

    if _is_probable_email(normalized_query):
        email_hash = search_data.get("email_hash")
        if email_hash and email_hash == make_search_hash(normalize_email(normalized_query)):
            return True
        return _matches_email_query(assertion, normalized_query)

    name_hash = search_data.get("name_hash")
    if name_hash and name_hash == make_search_hash(normalize_name(normalized_query)):
        return True

    return False


def _find_related_badges(assertion: dict[str, Any], current_assertion_id: str | None = None) -> list[dict[str, Any]]:
    search_data = assertion.get("search", {}) if isinstance(assertion.get("search"), dict) else {}
    email_hash = search_data.get("email_hash")
    name_hash = search_data.get("name_hash")

    matches: list[dict[str, Any]] = []
    for record in _list_badge_records():
        if current_assertion_id and record.get("assertion_id") == current_assertion_id:
            continue

        record_assertion = record.get("assertion", {}) if isinstance(record.get("assertion"), dict) else {}
        record_search = record_assertion.get("search", {}) if isinstance(record_assertion.get("search"), dict) else {}
        record_admin_recipient = record_assertion.get("admin_recipient", {}) if isinstance(record_assertion.get("admin_recipient"), dict) else {}

        same_email = bool(email_hash and record_search.get("email_hash") == email_hash)
        same_name = bool(name_hash and record_search.get("name_hash") == name_hash)

        if same_email or same_name:
            matches.append(
                {
                    "assertion_id": record.get("assertion_id"),
                    "badge_name": record.get("badge_name"),
                    "issuer_name": record.get("issuer_name"),
                    "issued_on": _format_display_date(record.get("issued_on")),
                    "recipient_name": record_admin_recipient.get("name") or None,
                    "recipient_email": record_admin_recipient.get("email") or None,
                    "json_url": record.get("json_url"),
                    "png_url": record.get("png_url"),
                    "verification_page_url": f"/verify/badge/{record.get('assertion_id')}",
                    "match": {
                        "email": same_email,
                        "name": same_name,
                    },
                }
            )

    return matches


def _format_display_date(value: Any) -> str:
    if not value:
        return "—"

    try:
        from datetime import datetime

        text_value = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text_value)
        return parsed.strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def _mask_email(value: Any) -> str:
    """Retourne une version non sensible d'une adresse email pour les pages publiques."""
    if not value or "@" not in str(value):
        return "Non disponible"

    local_part, domain = str(value).split("@", 1)
    if not local_part or not domain:
        return "Non disponible"

    visible_local = local_part[:2] if len(local_part) > 2 else local_part[:1]
    return f"{visible_local}…@{domain}"


def _build_issuer_check(assertion: dict[str, Any]) -> dict[str, Any]:
    issuer_ref = assertion.get("issuer", "")
    issuer_value = issuer_ref.get("id", "") if isinstance(issuer_ref, dict) else str(issuer_ref or "")
    canonical_mode83_issuer = "https://mode83.ddns.net/issuers/main"
    legacy_mode83_issuers = {
        "http://mode83.ddns.net:8000/issuers/main",
        "http://mode83.ddns.net/issuers/main",
    }
    local_issuer_url = f"{BASE_URL.rstrip('/')}/issuers/main"
    is_local = issuer_value in {local_issuer_url, canonical_mode83_issuer, *legacy_mode83_issuers}

    return {
        "issuer": issuer_value or "unknown",
        "is_local": is_local,
        "status": "local" if is_local else "external",
        "label": "mode83" if is_local else "autre organisme",
        "organization_label": "mode83" if is_local else "autre organisme",
        "message": (
            "Badge émis par mode83"
            if is_local
            else "Badge valide, mais émis par un autre organisme"
        ),
    }


def _build_proof_status(assertion_id: str, assertion: dict[str, Any]) -> dict[str, Any]:
    """Construit un résumé public de la preuve locale d'une assertion."""

    try:
        proof = ProofRepository().trouver_par_assertion(assertion_id)
    except Exception:
        return {
            "available": False,
            "status": "unavailable",
            "label": "Preuve locale indisponible",
            "tone": "warning",
            "message": "Le registre local des preuves n'est pas accessible pour le moment.",
            "credential_hash": None,
            "anchoring_status": "unavailable",
        }

    if not proof:
        return {
            "available": False,
            "status": "missing",
            "label": "Preuve locale absente",
            "tone": "warning",
            "message": "Aucune preuve hashée n'est encore associée à cette assertion.",
            "credential_hash": None,
            "anchoring_status": "not_requested",
        }

    current_hash = HashService().calculer_hash(assertion)
    stored_hash = proof.get("credential_hash")
    matches = stored_hash == current_hash
    return {
        "available": True,
        "matches": matches,
        "status": "matches" if matches else "mismatch",
        "label": "Preuve locale cohérente" if matches else "Preuve locale incohérente",
        "tone": "success" if matches else "danger",
        "message": (
            "Le hash actuel de l'assertion correspond à la preuve locale enregistrée."
            if matches
            else "Le hash actuel de l'assertion ne correspond pas à la preuve locale enregistrée."
        ),
        "credential_hash": stored_hash,
        "anchoring_status": proof.get("anchoring_status") or "not_requested",
        "created_at": proof.get("created_at"),
    }


def _build_revocation_status(assertion_id: str) -> dict[str, Any]:
    """Construit un résumé public du statut de révocation locale."""

    try:
        revocation = RevocationRepository().trouver(assertion_id)
    except Exception:
        return {
            "available": False,
            "revoked": False,
            "status": "unavailable",
            "label": "Statut credential indisponible",
            "public_label": "indisponible",
            "tone": "warning",
            "message": "Le registre local des révocations n'est pas accessible pour le moment.",
            "reason_category": None,
            "updated_at": None,
        }

    if revocation and revocation.get("revoked"):
        return {
            "available": True,
            "revoked": True,
            "status": "revoked",
            "label": "Credential révoqué",
            "public_label": "révoqué",
            "tone": "danger",
            "message": "Ce credential a été marqué comme révoqué dans le registre local Badge83.",
            "reason_category": revocation.get("reason_category"),
            "updated_at": revocation.get("updated_at"),
        }

    return {
        "available": True,
        "revoked": False,
        "status": "active",
        "label": "Credential actif",
        "public_label": "actif",
        "tone": "success",
        "message": "Aucune révocation locale n'est enregistrée pour ce credential.",
        "reason_category": None,
        "updated_at": None,
    }


def _build_blockchain_revocation_status(assertion_id: str) -> dict[str, Any]:
    """Construit un résumé public de la révocation blockchain, séparé de la révocation locale."""

    try:
        latest = BlockchainRevocationRepository().derniere_par_assertion(assertion_id)
    except Exception:
        return _blockchain_revocation_summary(None, unavailable=True)

    return _blockchain_revocation_summary(latest)


def _blockchain_revocation_summary(
    revocation: dict[str, Any] | None,
    *,
    unavailable: bool = False,
) -> dict[str, Any]:
    labels = {
        "revoked": "Révocation blockchain confirmée",
        "failed": "Révocation blockchain échouée",
        "not_configured": "Révocation blockchain non configurée",
        "not_requested": "Révocation blockchain non demandée",
        "unavailable": "Révocation blockchain indisponible",
    }
    tones = {
        "revoked": "success",
        "failed": "danger",
        "not_configured": "warning",
        "not_requested": "secondary",
        "unavailable": "warning",
    }
    if unavailable:
        status = "unavailable"
        provider = "evm"
        network = None
        tx_hash = None
        block_number = None
        updated_at = None
        error_message = None
    elif revocation is None:
        status = "not_requested"
        provider = "evm"
        network = None
        tx_hash = None
        block_number = None
        updated_at = None
        error_message = None
    else:
        status = str(revocation.get("status") or "not_requested")
        provider = str(revocation.get("provider") or "evm")
        network = revocation.get("network")
        tx_hash = revocation.get("tx_hash")
        block_number = revocation.get("block_number")
        updated_at = revocation.get("updated_at")
        error_message = revocation.get("error_message")

    return {
        "available": not unavailable,
        "provider": provider,
        "status": status,
        "revoked": status == "revoked",
        "label": labels.get(status, "Révocation blockchain inconnue"),
        "tone": tones.get(status, "secondary"),
        "network": network,
        "tx_hash": tx_hash,
        "explorer_tx_url": _build_evm_explorer_tx_url(tx_hash, provider),
        "block_number": block_number,
        "updated_at": updated_at,
        "error_message": error_message,
    }


def _build_anchoring_status(assertion_id: str) -> dict[str, Any]:
    """Construit un résumé public des ancrages locaux et EVM sans les opposer."""

    try:
        transactions = AnchoringRepository().lister_par_assertion(assertion_id)
    except Exception:
        unavailable = _anchoring_provider_status(None, provider="mock", unavailable=True)
        evm_unavailable = _anchoring_provider_status(None, provider="evm", unavailable=True)
        return {
            "available": False,
            "status": "unavailable",
            "label": "Ancrage indisponible",
            "tone": "warning",
            "message": "Le registre local d'ancrage n'est pas accessible pour le moment.",
            "provider": None,
            "network": None,
            "tx_hash": None,
            "explorer_tx_url": None,
            "block_number": None,
            "mock": unavailable,
            "evm": evm_unavailable,
            "blockchain_verification": _blockchain_verification_not_applicable(),
        }

    latest = transactions[-1] if transactions else None
    latest_mock = _latest_transaction_for_provider(transactions, "mock")
    latest_evm = _latest_transaction_for_provider(transactions, "evm")

    if latest is None:
        return {
            "available": True,
            "status": "not_requested",
            "label": "Ancrage non demandé",
            "tone": "secondary",
            "message": "Aucune demande d'ancrage locale ou EVM n'est enregistrée pour ce credential.",
            "provider": None,
            "network": None,
            "tx_hash": None,
            "explorer_tx_url": None,
            "block_number": None,
            "mock": _anchoring_provider_status(None, provider="mock"),
            "evm": _anchoring_provider_status(None, provider="evm"),
            "blockchain_verification": _blockchain_verification_not_applicable(),
        }

    summary_transaction = _select_anchoring_summary_transaction(latest_mock, latest_evm, latest)
    latest_status = _anchoring_provider_status(
        summary_transaction,
        provider=str(summary_transaction.get("provider") or "unknown"),
    )
    evm_status = _anchoring_provider_status(latest_evm, provider="evm")
    return {
        "available": True,
        "status": latest_status["status"],
        "label": latest_status["label"],
        "tone": latest_status["tone"],
        "message": "Dernier statut d'ancrage enregistré dans Badge83. Les statuts mock et EVM restent séparés.",
        "provider": summary_transaction.get("provider"),
        "network": summary_transaction.get("network"),
        "tx_hash": summary_transaction.get("tx_hash"),
        "explorer_tx_url": _build_evm_explorer_tx_url(summary_transaction.get("tx_hash"), summary_transaction.get("provider")),
        "block_number": summary_transaction.get("block_number"),
        "updated_at": summary_transaction.get("updated_at"),
        "latest_provider": latest.get("provider"),
        "latest_status": latest.get("status"),
        "mock": _anchoring_provider_status(latest_mock, provider="mock"),
        "evm": evm_status,
        "blockchain_verification": _build_blockchain_verification_status(latest_evm) if latest_evm else _blockchain_verification_not_applicable(),
    }


def _latest_transaction_for_provider(transactions: list[dict[str, Any]], provider: str) -> dict[str, Any] | None:
    for transaction in reversed(transactions):
        if transaction.get("provider") == provider:
            return transaction
    return None


def _select_anchoring_summary_transaction(
    latest_mock: dict[str, Any] | None,
    latest_evm: dict[str, Any] | None,
    latest: dict[str, Any],
) -> dict[str, Any]:
    """Choisit le statut résumé sans masquer un mock confirmé par un EVM échoué."""

    if latest_evm and latest_evm.get("status") == "anchored":
        return latest_evm
    if latest_mock and latest_mock.get("status") == "anchored":
        return latest_mock
    return latest


def _anchoring_provider_status(
    transaction: dict[str, Any] | None,
    *,
    provider: str,
    unavailable: bool = False,
) -> dict[str, Any]:
    labels = {
        "queued": "Ancrage en file d'attente",
        "pending": "Ancrage en cours",
        "anchored": "Ancrage confirmé",
        "failed": "Ancrage échoué",
        "retry_scheduled": "Nouvelle tentative planifiée",
        "not_requested": "Ancrage non demandé",
        "unavailable": "Ancrage indisponible",
    }
    tones = {
        "queued": "warning",
        "pending": "warning",
        "anchored": "success",
        "failed": "danger",
        "retry_scheduled": "warning",
        "not_requested": "secondary",
        "unavailable": "warning",
    }
    provider_labels = {
        "mock": "Ancrage local mock",
        "evm": "Ancrage blockchain EVM",
    }
    if unavailable:
        status = "unavailable"
        tx_hash = None
        network = None
        block_number = None
        updated_at = None
        error_message = None
    elif transaction is None:
        status = "not_requested"
        tx_hash = None
        network = None
        block_number = None
        updated_at = None
        error_message = None
    else:
        status = transaction.get("status") or "not_requested"
        tx_hash = transaction.get("tx_hash")
        network = transaction.get("network")
        block_number = transaction.get("block_number")
        updated_at = transaction.get("updated_at")
        error_message = transaction.get("error_message")

    return {
        "available": not unavailable,
        "provider": provider,
        "title": provider_labels.get(provider, f"Ancrage {provider}"),
        "status": status,
        "label": labels.get(status, "Ancrage inconnu"),
        "tone": tones.get(status, "secondary"),
        "network": network,
        "tx_hash": tx_hash,
        "explorer_tx_url": _build_evm_explorer_tx_url(tx_hash, provider),
        "block_number": block_number,
        "updated_at": updated_at,
        "error_message": error_message,
    }


def _build_evm_explorer_tx_url(tx_hash: Any, provider: Any) -> str | None:
    """Construit une URL explorer optionnelle sans exposer autre chose que le tx_hash."""

    if provider != "evm" or not isinstance(tx_hash, str) or not tx_hash.startswith("0x"):
        return None

    template = get_evm_explorer_tx_url_template()
    if not template or not template.startswith(("https://", "http://")):
        return None

    if "{tx_hash}" in template:
        return template.replace("{tx_hash}", tx_hash)
    return f"{template.rstrip('/')}/{tx_hash}"


def _blockchain_verification_not_applicable() -> dict[str, Any]:
    return {
        "available": False,
        "verified": False,
        "status": "not_applicable",
        "label": "Vérification blockchain non applicable",
        "tone": "secondary",
        "message": "Aucun ancrage EVM confirmé n'est disponible pour ce credential.",
        "provider": None,
        "network": None,
        "error_message": None,
    }


def _build_blockchain_verification_status(transaction: dict[str, Any]) -> dict[str, Any]:
    """Vérifie publiquement le hash EVM sans envoyer de donnée personnelle."""

    if transaction.get("provider") != "evm" or transaction.get("status") != "anchored":
        return _blockchain_verification_not_applicable()

    result = EvmAnchoringProvider().verifier_hash_ancre(str(transaction.get("credential_hash") or ""))
    status = str(result.get("status") or "unavailable")
    labels = {
        "verified": "Hash confirmé sur blockchain",
        "not_found_on_chain": "Hash absent du contrat EVM",
        "configuration_incomplete": "Vérification blockchain non configurée",
        "dependency_missing": "Dépendance blockchain absente",
        "rpc_unavailable": "RPC blockchain indisponible",
        "invalid_hash": "Hash credential invalide",
        "verification_failed": "Vérification blockchain échouée",
    }
    tones = {
        "verified": "success",
        "not_found_on_chain": "danger",
        "configuration_incomplete": "warning",
        "dependency_missing": "warning",
        "rpc_unavailable": "warning",
        "invalid_hash": "danger",
        "verification_failed": "warning",
    }
    verified = bool(result.get("verified"))
    return {
        **result,
        "label": labels.get(status, "Vérification blockchain indisponible"),
        "tone": tones.get(status, "warning"),
        "message": (
            "Le hash local du credential est présent dans le contrat EVM configuré."
            if verified
            else "La vérification blockchain est informative et n'expose que le hash du credential."
        ),
    }


def _publish_blockchain_revocation(
    assertion_id: str,
    credential_hash: str,
    *,
    provider: str = "evm",
    actor: str | None = None,
) -> dict[str, Any]:
    """Publie une révocation blockchain optionnelle et persiste le résultat sans bloquer le local."""

    provider_instance = get_anchoring_provider(provider)
    try:
        result = provider_instance.revoke({"assertion_id": assertion_id, "credential_hash": credential_hash})  # type: ignore[attr-defined]
    except Exception as exc:
        result = type(
            "FailedRevocationResult",
            (),
            {
                "status": "failed",
                "tx_hash": None,
                "block_number": None,
                "error_message": f"Erreur révocation blockchain : {exc}",
                "network": getattr(provider_instance, "network", None),
            },
        )()

    stored = BlockchainRevocationRepository().enregistrer(
        assertion_id=assertion_id,
        credential_hash=credential_hash,
        provider=getattr(provider_instance, "name", provider),
        network=result.network,
        status=result.status,
        tx_hash=result.tx_hash,
        block_number=result.block_number,
        error_message=result.error_message,
    )
    enregistrer_evenement_audit(
        "blockchain_revocation_completed" if result.status == "revoked" else "blockchain_revocation_failed",
        assertion_id=assertion_id,
        credential_hash=credential_hash,
        actor=actor,
        payload={
            "provider": getattr(provider_instance, "name", provider),
            "network": result.network,
            "status": result.status,
            "tx_hash": result.tx_hash,
            "error_message": result.error_message,
        },
    )
    return stored


def _build_audit_trail(assertion_id: str) -> dict[str, Any]:
    """Construit un résumé admin des événements d'audit associés à un badge."""

    try:
        events = AuditRepository().lister_par_assertion(assertion_id)
    except Exception:
        return {
            "available": False,
            "count": 0,
            "latest_event_type": None,
            "items": [],
        }

    return {
        "available": True,
        "count": len(events),
        "latest_event_type": events[-1].get("event_type") if events else None,
        "items": events,
    }


def _collect_badge_record(assertion_id: str, assertion: dict[str, Any] | None = None) -> dict[str, Any] | None:
    json_path = ISSUED_DIR / f"{assertion_id}.json"
    png_path = BAKED_DIR / f"{assertion_id}.png"

    if assertion is None and json_path.exists():
        assertion = _safe_load_json(json_path)

    if assertion is None:
        return None

    recipient = assertion.get("recipient", {}) if isinstance(assertion.get("recipient"), dict) else {}
    verification = assertion.get("verification", {}) if isinstance(assertion.get("verification"), dict) else {}
    admin_recipient = assertion.get("admin_recipient", {}) if isinstance(assertion.get("admin_recipient"), dict) else {}
    compliance = check_assertion(assertion)
    proof_status = _build_proof_status(assertion_id, assertion)
    revocation_status = _build_revocation_status(assertion_id)
    anchoring_status = _build_anchoring_status(assertion_id)
    blockchain_revocation_status = _build_blockchain_revocation_status(assertion_id)
    audit_trail = _build_audit_trail(assertion_id)

    badge_ref = assertion.get("badge", "")
    issuer_ref = assertion.get("issuer", "")
    badge_name = badge_ref.split("/")[-1].replace("-", " ").title() if isinstance(badge_ref, str) and badge_ref else "Unknown"
    issuer_name = issuer_ref.split("/")[-1].replace("-", " ").title() if isinstance(issuer_ref, str) and issuer_ref else "Unknown"

    return {
        "assertion_id": assertion_id,
        "issued_on": assertion.get("issuedOn"),
        "issued_on_display": _format_display_date(assertion.get("issuedOn")),
        "name": admin_recipient.get("name"),
        "email": admin_recipient.get("email"),
        "has_json": json_path.exists(),
        "has_png": png_path.exists(),
        "json_url": f"/api/badges/{assertion_id}/json",
        "png_url": f"/api/badges/{assertion_id}/png",
        "public_assertion_url": assertion.get("url") or assertion.get("id"),
        "badge_name": badge_name,
        "issuer_name": issuer_name,
        "recipient": {
            "type": recipient.get("type"),
            "identity": recipient.get("identity"),
            "hashed": recipient.get("hashed"),
            "salt": recipient.get("salt"),
        },
        "verification": verification,
        "compliance": compliance,
        "proof": proof_status,
        "credential_status": revocation_status,
        "anchoring": anchoring_status,
        "blockchain_revocation": blockchain_revocation_status,
        "audit": audit_trail,
        "search": {
            "has_name_hash": bool(assertion.get("search", {}).get("name_hash")) if isinstance(assertion.get("search"), dict) else False,
            "has_email_hash": bool(assertion.get("search", {}).get("email_hash")) if isinstance(assertion.get("search"), dict) else False,
        },
        "assertion": assertion,
    }


def _list_badge_records() -> list[dict[str, Any]]:
    ISSUED_DIR.mkdir(parents=True, exist_ok=True)
    BAKED_DIR.mkdir(parents=True, exist_ok=True)

    assertion_ids = {path.stem for path in ISSUED_DIR.glob("*.json")}
    assertion_ids.update(path.stem for path in BAKED_DIR.glob("*.png"))

    records: list[dict[str, Any]] = []
    for assertion_id in sorted(assertion_ids):
        record = _collect_badge_record(assertion_id)
        if record:
            records.append(record)

    records.sort(key=lambda item: item.get("issued_on") or "", reverse=True)
    return records


def _dashboard_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    hosted_count = sum(1 for record in records if str(record.get("public_assertion_url", "")).startswith("http"))
    return {
        "total_badges": len(records),
        "total_json": sum(1 for record in records if record.get("has_json")),
        "total_png": sum(1 for record in records if record.get("has_png")),
        "hosted_ready": hosted_count,
        "base_url": BASE_URL,
        "latest_badge": records[0]["assertion_id"] if records else None,
    }


@app.get("/api/dashboard/stats", dependencies=[Depends(require_admin)])
async def api_dashboard_stats():
    records = _list_badge_records()
    return _dashboard_stats(records)


@app.get("/api/badges", dependencies=[Depends(require_admin)])
async def api_list_badges():
    records = _list_badge_records()
    return {"items": records, "stats": _dashboard_stats(records)}


@app.get("/api/badges/search", dependencies=[Depends(require_admin)])
async def api_search_badges(query: str):
    records = _list_badge_records()
    matched = [record for record in records if _matches_search_query(record, query)]
    return {
        "items": matched,
        "stats": _dashboard_stats(matched),
        "query": query,
        "mode": "email" if _is_probable_email(query) else "name-or-text",
    }


@app.post("/api/verify-desk/png", dependencies=[Depends(require_admin)])
async def api_verify_desk_png(badge: UploadFile = File(...)):
    """Workflow simplifié : upload PNG, vérification et recherche de certificats liés."""
    png_data = await read_upload_limited(badge, get_max_png_upload_bytes(), label="PNG")
    ensure_image_pixels_within_limit(png_data, label="PNG")
    result = verify_baked_badge(png_data)

    if not result.get("valid"):
        return {
            "valid": False,
            "error": result.get("error", "Impossible de vérifier le PNG"),
            "summary": None,
            "related_badges": [],
        }

    assertion = result.get("assertion") or {}
    assertion_id = _extract_assertion_id(assertion)
    related_badges = _find_related_badges(assertion, current_assertion_id=assertion_id)
    search_data = assertion.get("search", {}) if isinstance(assertion.get("search"), dict) else {}
    admin_recipient = assertion.get("admin_recipient", {}) if isinstance(assertion.get("admin_recipient"), dict) else {}

    return {
        "valid": True,
        "summary": result.get("summary"),
        "assertion_id": assertion_id,
        "assertion": assertion,
        "issuer_check": _build_issuer_check(assertion),
        "recipient_display": {
            "name": admin_recipient.get("name") or "Non disponible",
            "email": admin_recipient.get("email") or "Non disponible",
            "issued_on": _format_display_date(assertion.get("issuedOn")),
        },
        "related_badges": related_badges,
        "search_capabilities": {
            "has_email_hash": bool(search_data.get("email_hash")),
            "has_name_hash": bool(search_data.get("name_hash")),
            "can_find_related_by_email": bool(search_data.get("email_hash")),
            "can_find_related_by_name": bool(search_data.get("name_hash")),
        },
    }


@app.get("/api/badges/{assertion_id}", dependencies=[Depends(require_admin)])
async def api_get_badge(assertion_id: str):
    record = _collect_badge_record(assertion_id)
    if not record:
        raise HTTPException(status_code=404, detail="Badge introuvable")

    png_inspection = None
    png_path = BAKED_DIR / f"{assertion_id}.png"
    if png_path.exists():
        png_inspection = verify_baked_badge(png_path.read_bytes())

    return {
        **record,
        "png_preview_url": record["png_url"] if record.get("has_png") else None,
        "png_inspection": png_inspection,
    }


@app.get("/api/badges/{assertion_id}/proof", dependencies=[Depends(require_admin)])
async def api_get_badge_proof(assertion_id: str):
    """Retourne la preuve locale associée à un badge."""

    proof = ProofRepository().trouver_par_assertion(assertion_id)
    if not proof:
        raise HTTPException(status_code=404, detail="Preuve locale introuvable")

    return {
        "assertion_id": proof["assertion_id"],
        "proof_version": proof["proof_version"],
        "hash_algorithm": proof["hash_algorithm"],
        "canonicalization": proof["canonicalization"],
        "credential_hash": proof["credential_hash"],
        "anchoring_status": proof["anchoring_status"],
        "created_at": proof["created_at"],
        "updated_at": proof["updated_at"],
    }


@app.post("/api/badges/{assertion_id}/revoke", dependencies=[Depends(require_admin)])
async def api_revoke_badge(assertion_id: str, payload: dict[str, Any] | None = Body(default=None)):
    """Marque un badge comme révoqué localement, avec publication blockchain optionnelle."""

    if _collect_badge_record(assertion_id) is None:
        raise HTTPException(status_code=404, detail="Badge introuvable")

    payload = payload or {}
    revocation = RevocationRepository().revoquer(
        assertion_id,
        reason_category=payload.get("reason_category"),
        actor=payload.get("actor") or "admin",
    )
    proof = ProofRepository().trouver_par_assertion(assertion_id)
    enregistrer_evenement_audit(
        "credential_revoked",
        assertion_id=assertion_id,
        credential_hash=proof.get("credential_hash") if proof else None,
        actor=revocation.get("actor"),
        payload={"reason_category": revocation.get("reason_category")},
    )
    blockchain_revocation = None
    if payload.get("request_evm_revocation") is True:
        if proof and proof.get("credential_hash"):
            blockchain_revocation = _publish_blockchain_revocation(
                assertion_id,
                str(proof["credential_hash"]),
                provider=str(payload.get("blockchain_provider") or "evm"),
                actor=revocation.get("actor"),
            )
        else:
            blockchain_revocation = BlockchainRevocationRepository().enregistrer(
                assertion_id=assertion_id,
                credential_hash="",
                provider=str(payload.get("blockchain_provider") or "evm"),
                status="failed",
                error_message="Preuve locale introuvable : révocation blockchain impossible.",
            )
    return {
        "assertion_id": revocation["assertion_id"],
        "revoked": revocation["revoked"],
        "reason_category": revocation["reason_category"],
        "actor": revocation["actor"],
        "created_at": revocation["created_at"],
        "updated_at": revocation["updated_at"],
        "blockchain_revocation": _blockchain_revocation_summary(blockchain_revocation),
    }


@app.get("/api/badges/{assertion_id}/revocation", dependencies=[Depends(require_admin)])
async def api_get_badge_revocation(assertion_id: str):
    """Retourne le statut de révocation locale associé à un badge."""

    if _collect_badge_record(assertion_id) is None:
        raise HTTPException(status_code=404, detail="Badge introuvable")

    revocation_status = _build_revocation_status(assertion_id)
    return {
        "assertion_id": assertion_id,
        **revocation_status,
        "blockchain_revocation": _build_blockchain_revocation_status(assertion_id),
    }


@app.post("/api/badges/{assertion_id}/revoke/blockchain", dependencies=[Depends(require_admin)])
async def api_revoke_badge_blockchain(assertion_id: str, payload: dict[str, Any] | None = Body(default=None)):
    """Publie explicitement la révocation EVM d'un badge déjà révoqué localement."""

    if _collect_badge_record(assertion_id) is None:
        raise HTTPException(status_code=404, detail="Badge introuvable")
    if not RevocationRepository().est_revoque(assertion_id):
        raise HTTPException(status_code=409, detail="Révocation locale requise avant publication blockchain")
    proof = ProofRepository().trouver_par_assertion(assertion_id)
    if not proof:
        raise HTTPException(status_code=404, detail="Preuve locale introuvable")

    payload = payload or {}
    stored = _publish_blockchain_revocation(
        assertion_id,
        str(proof["credential_hash"]),
        provider=str(payload.get("provider") or "evm"),
        actor=payload.get("actor") or "admin",
    )
    return {
        "assertion_id": assertion_id,
        "blockchain_revocation": _blockchain_revocation_summary(stored),
    }


@app.post("/api/badges/{assertion_id}/anchor", dependencies=[Depends(require_admin)])
async def api_anchor_badge(assertion_id: str, payload: dict[str, Any] | None = Body(default=None)):
    """Crée et traite une demande d'ancrage local pour un badge."""

    if _collect_badge_record(assertion_id) is None:
        raise HTTPException(status_code=404, detail="Badge introuvable")

    payload = payload or {}
    provider = payload.get("provider") or get_default_anchoring_provider()
    actor = payload.get("actor") or "admin"
    process_immediately = payload.get("process", True)
    service = AnchoringService()

    try:
        transaction = service.demander_ancrage(assertion_id, provider=provider, actor=actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if process_immediately:
        transaction = service.traiter_transaction(transaction["id"], provider=provider, actor=actor)

    return {
        "assertion_id": assertion_id,
        "transaction": transaction,
    }


@app.get("/api/badges/{assertion_id}/anchoring", dependencies=[Depends(require_admin)])
async def api_get_badge_anchoring(assertion_id: str):
    """Retourne les transactions d'ancrage locales associées à un badge."""

    if _collect_badge_record(assertion_id) is None:
        raise HTTPException(status_code=404, detail="Badge introuvable")

    transactions = AnchoringRepository().lister_par_assertion(assertion_id)
    latest = transactions[-1] if transactions else None
    latest_mock = _latest_transaction_for_provider(transactions, "mock")
    latest_evm = _latest_transaction_for_provider(transactions, "evm")
    summary = _select_anchoring_summary_transaction(latest_mock, latest_evm, latest) if latest else None
    return {
        "assertion_id": assertion_id,
        "latest_status": summary.get("status") if summary else "not_requested",
        "latest_provider": summary.get("provider") if summary else None,
        "mock": _anchoring_provider_status(latest_mock, provider="mock"),
        "evm": _anchoring_provider_status(latest_evm, provider="evm"),
        "items": transactions,
    }


@app.get("/api/badges/{assertion_id}/audit", dependencies=[Depends(require_admin)])
async def api_get_badge_audit(assertion_id: str):
    """Retourne l'historique d'audit local associé à un badge."""

    if _collect_badge_record(assertion_id) is None:
        raise HTTPException(status_code=404, detail="Badge introuvable")

    audit_trail = _build_audit_trail(assertion_id)
    return {
        "assertion_id": assertion_id,
        **audit_trail,
    }


@app.get("/api/badges/{assertion_id}/json", dependencies=[Depends(require_admin)])
async def api_download_badge_json(assertion_id: str):
    file_path = ISSUED_DIR / f"{assertion_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="JSON du badge introuvable")
    return FileResponse(file_path, media_type="application/json", filename=f"{assertion_id}.json")


@app.get("/api/badges/{assertion_id}/png", dependencies=[Depends(require_admin)])
async def api_download_badge_png(assertion_id: str):
    file_path = BAKED_DIR / f"{assertion_id}.png"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PNG du badge introuvable")
    return FileResponse(file_path, media_type="image/png", filename=f"{assertion_id}.png")


@app.get("/api/badges/{assertion_id}/inspect", dependencies=[Depends(require_admin)])
async def api_inspect_badge_png(assertion_id: str):
    file_path = BAKED_DIR / f"{assertion_id}.png"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PNG du badge introuvable")
    return verify_baked_badge(file_path.read_bytes())


@app.put("/api/badges/{assertion_id}", dependencies=[Depends(require_admin)])
async def api_update_badge(assertion_id: str, payload: dict[str, Any] = Body(...)):
    file_path = ISSUED_DIR / f"{assertion_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Badge introuvable")

    assertion = _safe_load_json(file_path)
    if not assertion or assertion.get("type") != "Assertion":
        raise HTTPException(status_code=400, detail="Assertion de badge invalide")

    updated_assertion = payload.get("assertion") if isinstance(payload.get("assertion"), dict) else payload
    if updated_assertion.get("type") != "Assertion":
        raise HTTPException(status_code=400, detail="La charge utile doit être une assertion Open Badges")

    updated_assertion["id"] = assertion.get("id")
    if assertion.get("url"):
        updated_assertion["url"] = assertion.get("url")

    file_path.write_text(json.dumps(updated_assertion, ensure_ascii=False, indent=2), encoding="utf-8")
    sync_assertion_record(assertion_id, updated_assertion)
    record = _collect_badge_record(assertion_id, updated_assertion)
    return {"status": "updated", "item": record}


@app.delete("/api/badges/{assertion_id}", dependencies=[Depends(require_admin)])
async def api_delete_badge(assertion_id: str):
    json_path = ISSUED_DIR / f"{assertion_id}.json"
    png_path = BAKED_DIR / f"{assertion_id}.png"

    deleted = []
    if json_path.exists():
        json_path.unlink()
        delete_assertion_record(assertion_id)
        deleted.append("json")
    if png_path.exists():
        png_path.unlink()
        deleted.append("png")

    if not deleted:
        raise HTTPException(status_code=404, detail="Badge introuvable")

    return {"status": "deleted", "assertion_id": assertion_id, "deleted": deleted}


# ---------------------------------------------------------------------------
# Endpoints publics pour la vérification HostedBadge (Open Badges 2.0)
# ---------------------------------------------------------------------------

def _serve_json_file(file_path: Path) -> JSONResponse:
    """Fonction utilitaire pour servir un fichier JSON avec le bon type de contenu Open Badges."""
    if not file_path.exists():
        return JSONResponse(status_code=404, content={"error": "Ressource introuvable"})
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return JSONResponse(content=data, media_type=OB_CONTENT_TYPE)


def _serve_template_json(template_name: str) -> JSONResponse:
    """Sert un fichier de template JSON avec remplacement du placeholder ${BASE_URL}."""
    template_path = DATA_BASE / template_name
    if not template_path.exists():
        return JSONResponse(status_code=404, content={"error": "Ressource introuvable"})
    content = template_path.read_text(encoding="utf-8")
    content = content.replace("${BASE_URL}", BASE_URL)
    data = json.loads(content)
    return JSONResponse(content=data, media_type=OB_CONTENT_TYPE)


@app.get("/issuers/{issuer_id}")
async def get_issuer(issuer_id: str):
    """Sert le profil de l'émetteur à une URL publique.

    URL attendue : {BASE_URL}/issuers/main
    """
    return _serve_template_json("issuer_template.json")


@app.get("/badges/{badge_slug}")
async def get_badge_class(badge_slug: str):
    """Sert la définition du badge à une URL publique.

    URL attendue : {BASE_URL}/badges/blockchain-foundations
    """
    return _serve_template_json("badgeclass_template.json")


@app.get("/assertions/{assertion_id}")
async def get_assertion(assertion_id: str):
    """Sert une assertion Open Badges à une URL publique.

    URL attendue : {BASE_URL}/assertions/<uuid>
    """
    return _serve_json_file(DATA_BASE / "issued" / f"{assertion_id}.json")


@app.get("/assets/{asset_name}")
async def get_asset(asset_name: str):
    """Sert les assets statiques (images de badge, logo émetteur, etc.)."""
    if "/" in asset_name or "\\" in asset_name or asset_name in {".", ".."}:
        return JSONResponse(status_code=400, content={"error": "Nom d'asset invalide"})

    base_dir = DATA_BASE.resolve()
    asset_path = (base_dir / asset_name).resolve()
    if not asset_path.is_relative_to(base_dir):
        return JSONResponse(status_code=400, content={"error": "Nom d'asset invalide"})
    if not asset_path.exists() or not asset_path.is_file():
        return JSONResponse(status_code=404, content={"error": "Asset introuvable"})
    return FileResponse(asset_path, media_type="image/png")


# ---------------------------------------------------------------------------
# Vérification en ligne — résoudre les URLs publiques et valider la chaîne complète
# ---------------------------------------------------------------------------

async def _fetch_url(url: str) -> dict | None:
    """Récupère une URL publique et retourne le JSON parsé, ou None en cas d'échec."""
    try:
        current_url = validate_public_http_url(url)
        headers = {"Accept": "application/ld+json, application/json;q=0.9, */*;q=0.1"}
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            for _ in range(MAX_REMOTE_REDIRECTS + 1):
                async with client.stream("GET", current_url, headers=headers) as resp:
                    if resp.is_redirect:
                        location = resp.headers.get("location")
                        if not location:
                            return None
                        current_url = validate_public_http_url(str(resp.url.join(location)))
                        continue
                    if resp.status_code != 200:
                        return None
                    content = b""
                    async for chunk in resp.aiter_bytes():
                        content += chunk
                        if len(content) > MAX_REMOTE_JSON_BYTES:
                            return None
                    return json.loads(content.decode(resp.encoding or "utf-8"))
    except (SSRFProtectionError, Exception):
        return None
    return None


@app.post("/verify-online")
async def verify_online(
    assertion_url: str | None = Form(None),
    badge_file: UploadFile | None = File(None),
):
    """Vérifie un badge en résolvant toutes les URLs publiques de la chaîne.

    Accepte soit une URL d'assertion, soit un fichier PNG baked.
    Retourne l'assertion + l'état de chaque ressource référencée.
    """
    assertion = None

    # Cas 1 : l'utilisateur a téléversé un PNG baked
    if badge_file:
        png_data = await read_upload_limited(badge_file, get_max_png_upload_bytes(), label="PNG")
        ensure_image_pixels_within_limit(png_data, label="PNG")
        from app.verifier import verify_baked_badge
        result = verify_baked_badge(png_data)
        if not result["valid"]:
            return {"valid": False, "error": result.get("error", "Échec de l'extraction de l'assertion")}
        assertion = result["assertion"]

    # Cas 2 : l'utilisateur a fourni une URL d'assertion
    elif assertion_url:
        assertion = await _fetch_url(assertion_url)
        if not assertion or assertion.get("type") != "Assertion":
            return {"valid": False, "error": "Impossible de récupérer une assertion valide depuis cette URL"}
    else:
        return JSONResponse(
            status_code=400,
            content={"error": "Fournissez soit assertion_url, soit badge_file"},
        )

    # Résoudre la chaîne complète : URL du badge → BadgeClass, URL de l'émetteur → Issuer
    badge_ref = assertion.get("badge", "")
    issuer_ref = assertion.get("issuer", "")

    badge_data = None
    issuer_data = None

    if isinstance(badge_ref, str) and badge_ref.startswith("http"):
        badge_data = await _fetch_url(badge_ref)
    if isinstance(issuer_ref, str) and issuer_ref.startswith("http"):
        issuer_data = await _fetch_url(issuer_ref)

    # Contrôle croisé : BadgeClass.issuer doit correspondre à assertion.issuer
    chain_valid = True
    chain_notes = []

    if badge_data is None and isinstance(badge_ref, str):
        chain_valid = False
        chain_notes.append(f"BadgeClass inaccessible : {badge_ref}")
    if issuer_data is None and isinstance(issuer_ref, str):
        chain_valid = False
        chain_notes.append(f"Issuer inaccessible : {issuer_ref}")

    if badge_data and issuer_ref:
        badge_issuer = badge_data.get("issuer", "")
        if isinstance(badge_issuer, str) and badge_issuer != issuer_ref:
            chain_valid = False
            chain_notes.append("BadgeClass.issuer ne correspond pas à assertion.issuer")

    if not chain_notes:
        chain_notes.append("Chaîne complète validée")

    return {
        "valid": chain_valid,
        "assertion": assertion,
        "chain": {
            "badge_class": badge_data,
            "issuer": issuer_data,
            "notes": chain_notes,
        },
        "summary": {
            "assertion_id": assertion.get("id", "unknown"),
            "badge_name": badge_ref.split("/")[-1].replace("-", " ").title() if isinstance(badge_ref, str) else "unknown",
            "issuer_name": issuer_ref.split("/")[-1].title() if isinstance(issuer_ref, str) else "unknown",
            "recipient_name": assertion.get("recipient", {}).get("name", "unknown"),
            "issued_on": assertion.get("issuedOn"),
        },
    }
