from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


OPEN_BADGES_CONTEXT = "https://w3id.org/openbadges/v2"
SHA256_PREFIX = "sha256$"


def _new_report() -> dict[str, Any]:
    return {
        "valid": True,
        "errorCount": 0,
        "warningCount": 0,
        "messages": [],
        "checks": [],
    }


def _add_check(
    report: dict[str, Any],
    name: str,
    ok: bool,
    message: str,
    *,
    severity: str = "error",
    details: dict[str, Any] | None = None,
) -> None:
    """Ajoute un contrôle structuré au rapport de conformité local."""
    normalized_severity = severity if severity in {"error", "warning", "info"} else "error"
    check = {
        "name": name,
        "ok": ok,
        "severity": normalized_severity,
        "message": message,
    }
    if details:
        check["details"] = details
    report["checks"].append(check)

    if ok:
        return

    report["messages"].append(message)
    if normalized_severity == "warning":
        report["warningCount"] += 1
    elif normalized_severity == "error":
        report["errorCount"] += 1
        report["valid"] = False


def _has_context(document: dict[str, Any]) -> bool:
    context = document.get("@context")
    if isinstance(context, str):
        return context == OPEN_BADGES_CONTEXT
    if isinstance(context, list):
        return OPEN_BADGES_CONTEXT in context
    return False


def _is_http_url(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _document_url(document: Any) -> str | None:
    if isinstance(document, str):
        return document if _is_http_url(document) else None
    if isinstance(document, dict):
        for key in ("id", "url"):
            value = document.get(key)
            if _is_http_url(value):
                return value
    return None


def _document_type(document: Any) -> str | None:
    if isinstance(document, dict):
        value = document.get("type")
        return value if isinstance(value, str) else None
    return None


def _looks_like_sha256_identity(identity: Any) -> bool:
    if not isinstance(identity, str) or not identity.startswith(SHA256_PREFIX):
        return False
    digest = identity.removeprefix(SHA256_PREFIX)
    return len(digest) == 64 and all(char in "0123456789abcdefABCDEF" for char in digest)


def _normalize_origin(value: str) -> str:
    parsed = urlparse(value if "://" in value else f"https://{value}")
    host = parsed.netloc or parsed.path
    return host.lower().rstrip("/")


def _url_matches_allowed_origins(url: str, allowed_origins: list[Any]) -> bool:
    assertion_origin = _normalize_origin(url)
    return any(isinstance(origin, str) and assertion_origin == _normalize_origin(origin) for origin in allowed_origins)


def _url_matches_starts_with(url: str, starts_with: list[Any]) -> bool:
    return any(isinstance(prefix, str) and url.startswith(prefix) for prefix in starts_with)


def check_assertion(assertion: dict[str, Any] | None) -> dict[str, Any]:
    """Contrôle local minimal d'une Assertion Open Badges 2.0."""
    report = _new_report()
    if not isinstance(assertion, dict):
        _add_check(report, "assertion.document", False, "Assertion absente ou illisible.")
        return report

    _add_check(report, "assertion.context", _has_context(assertion), "Contexte Open Badges 2.0 présent.")
    _add_check(report, "assertion.type", assertion.get("type") == "Assertion", "Type Assertion attendu.")
    _add_check(report, "assertion.id", _is_http_url(assertion.get("id")) or _is_http_url(assertion.get("url")), "Identifiant public HTTP(S) présent.")
    _add_check(report, "assertion.badge", _document_url(assertion.get("badge")) is not None, "Référence BadgeClass HTTP(S) présente.")
    _add_check(report, "assertion.issuer", _document_url(assertion.get("issuer")) is not None, "Référence Issuer HTTP(S) présente.")
    _add_check(report, "assertion.issuedOn", isinstance(assertion.get("issuedOn"), str) and bool(assertion.get("issuedOn")), "Date issuedOn présente.")

    expires = assertion.get("expires")
    _add_check(
        report,
        "assertion.expires",
        expires is None or isinstance(expires, str),
        "Date expires absente ou au format texte.",
        severity="warning",
    )

    recipient = assertion.get("recipient") if isinstance(assertion.get("recipient"), dict) else {}
    _add_check(report, "recipient.hashed", recipient.get("hashed") is True, "Identité du destinataire hashée.")
    _add_check(report, "recipient.identity", _looks_like_sha256_identity(recipient.get("identity")), "Identité au format sha256$... valide.")

    verification = assertion.get("verification") if isinstance(assertion.get("verification"), dict) else {}
    _add_check(report, "verification.type", verification.get("type") == "HostedBadge", "Vérification HostedBadge déclarée.")
    return report


def check_badgeclass(badgeclass: dict[str, Any] | None, assertion: dict[str, Any] | None = None) -> dict[str, Any]:
    """Contrôle local minimal d'une BadgeClass."""
    report = _new_report()
    if not isinstance(badgeclass, dict):
        _add_check(report, "badgeclass.document", False, "BadgeClass absente ou illisible.")
        return report

    _add_check(report, "badgeclass.context", _has_context(badgeclass), "Contexte Open Badges 2.0 présent.")
    _add_check(report, "badgeclass.type", badgeclass.get("type") == "BadgeClass", "Type BadgeClass attendu.")
    _add_check(report, "badgeclass.id", _is_http_url(badgeclass.get("id")), "Identifiant BadgeClass HTTP(S) présent.")
    _add_check(report, "badgeclass.name", isinstance(badgeclass.get("name"), str) and bool(badgeclass.get("name")), "Nom de badge présent.")
    _add_check(report, "badgeclass.description", isinstance(badgeclass.get("description"), str) and bool(badgeclass.get("description")), "Description de badge présente.")
    _add_check(report, "badgeclass.image", _is_http_url(badgeclass.get("image")), "Image de badge HTTP(S) présente.")
    _add_check(report, "badgeclass.criteria", isinstance(badgeclass.get("criteria"), dict), "Critères de badge présents.")
    _add_check(report, "badgeclass.issuer", _document_url(badgeclass.get("issuer")) is not None, "Référence Issuer HTTP(S) présente.")

    if isinstance(assertion, dict):
        assertion_badge_url = _document_url(assertion.get("badge"))
        _add_check(
            report,
            "badgeclass.matches_assertion",
            assertion_badge_url is None or badgeclass.get("id") == assertion_badge_url,
            "BadgeClass cohérente avec la référence de l'assertion.",
        )
    return report


def check_issuer(
    issuer: dict[str, Any] | None,
    assertion: dict[str, Any] | None = None,
    badgeclass: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Contrôle local minimal d'un Issuer et de ses règles de vérification."""
    report = _new_report()
    if not isinstance(issuer, dict):
        _add_check(report, "issuer.document", False, "Issuer absent ou illisible.")
        return report

    _add_check(report, "issuer.context", _has_context(issuer), "Contexte Open Badges 2.0 présent.")
    _add_check(report, "issuer.type", issuer.get("type") == "Issuer", "Type Issuer attendu.")
    _add_check(report, "issuer.id", _is_http_url(issuer.get("id")), "Identifiant Issuer HTTP(S) présent.")
    _add_check(report, "issuer.name", isinstance(issuer.get("name"), str) and bool(issuer.get("name")), "Nom de l'émetteur présent.")
    _add_check(report, "issuer.url", _is_http_url(issuer.get("url")), "URL publique de l'émetteur présente.")

    if isinstance(badgeclass, dict):
        _add_check(
            report,
            "issuer.matches_badgeclass",
            _document_url(badgeclass.get("issuer")) == issuer.get("id"),
            "Issuer cohérent avec BadgeClass.issuer.",
        )

    verification = issuer.get("verification") if isinstance(issuer.get("verification"), dict) else {}
    allowed_origins = verification.get("allowedOrigins") if isinstance(verification.get("allowedOrigins"), list) else []
    starts_with = verification.get("startsWith") if isinstance(verification.get("startsWith"), list) else []
    assertion_url = _document_url(assertion.get("id") if isinstance(assertion, dict) else None) if isinstance(assertion, dict) else None

    _add_check(report, "issuer.allowedOrigins", bool(allowed_origins), "allowedOrigins déclaré par l'émetteur.", severity="warning")
    _add_check(report, "issuer.startsWith", bool(starts_with), "startsWith déclaré par l'émetteur.", severity="warning")
    if assertion_url and allowed_origins:
        _add_check(report, "issuer.allowedOrigins.matches", _url_matches_allowed_origins(assertion_url, allowed_origins), "Origine de l'assertion autorisée par l'émetteur.")
    if assertion_url and starts_with:
        _add_check(report, "issuer.startsWith.matches", _url_matches_starts_with(assertion_url, starts_with), "URL de l'assertion conforme au préfixe autorisé.")
    return report


def merge_reports(*reports: dict[str, Any] | None) -> dict[str, Any]:
    """Fusionne plusieurs rapports de conformité en conservant les détails."""
    merged = _new_report()
    for report in reports:
        if not isinstance(report, dict):
            continue
        merged["checks"].extend(report.get("checks", []))
        merged["messages"].extend(report.get("messages", []))
        merged["errorCount"] += int(report.get("errorCount", 0) or 0)
        merged["warningCount"] += int(report.get("warningCount", 0) or 0)
    merged["valid"] = merged["errorCount"] == 0
    return merged


def check_openbadges_chain(
    assertion: dict[str, Any] | None,
    badgeclass: dict[str, Any] | None = None,
    issuer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Produit un rapport local Assertion + BadgeClass + Issuer."""
    return merge_reports(
        check_assertion(assertion),
        check_badgeclass(badgeclass, assertion) if badgeclass is not None else None,
        check_issuer(issuer, assertion, badgeclass) if issuer is not None else None,
    )