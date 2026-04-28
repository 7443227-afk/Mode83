from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx

from app.baker import unbake_badge
from app.config import ISSUED_DIR as DATA_DIR


def verify_badge(badge_id: str) -> dict:
    """Vérifie si une Assertion Open Badges 2.0 existe et retourne son état avec ses données."""
    badge_path = DATA_DIR / f"{badge_id}.json"
    if not badge_path.exists():
        return {"valid": False, "assertion": None}

    with badge_path.open("r", encoding="utf-8") as file:
        badge_data = json.load(file)

    if badge_data.get("type") != "Assertion":
        return {"valid": False, "assertion": None}

    badge_ref = badge_data.get("badge", "")
    issuer_ref = badge_data.get("issuer", "")

    # Handle both URL references (string) and embedded objects (dict)
    if isinstance(badge_ref, str):
        badge_name = badge_ref.split("/")[-1].replace("-", " ").title()
    else:
        badge_name = badge_ref.get("name", "unknown")

    if isinstance(issuer_ref, str):
        issuer_name = issuer_ref.split("/")[-1].replace("-", " ").title()
    else:
        issuer_name = issuer_ref.get("name", "unknown")

    return {
        "valid": True,
        "assertion": badge_data,
        "summary": {
            "assertion_id": badge_id,
            "badge_name": badge_name,
            "issuer_name": issuer_name,
            "recipient_name": badge_data.get("recipient", {}).get("name", "unknown"),
            "issued_on": badge_data.get("issuedOn"),
        },
    }


def verify_baked_badge(png_data: bytes) -> dict:
    """Extrait l'assertion d'un PNG baked et la vérifie."""
    try:
        assertion = unbake_badge(png_data)
    except (ValueError, Exception) as exc:
        return {"valid": False, "error": str(exc), "assertion": None}

    if assertion.get("type") != "Assertion":
        return {"valid": False, "error": "Ce document n'est pas une assertion Open Badges valide", "assertion": None}

    badge_id = assertion.get("id", "unknown")
    badge_ref = assertion.get("badge", "")
    issuer_ref = assertion.get("issuer", "")

    # Handle both URL references (string) and embedded objects (dict)
    if isinstance(badge_ref, str):
        badge_name = badge_ref.split("/")[-1].replace("-", " ").title()
    else:
        badge_name = badge_ref.get("name", "unknown")

    if isinstance(issuer_ref, str):
        issuer_name = issuer_ref.split("/")[-1].replace("-", " ").title()
    else:
        issuer_name = issuer_ref.get("name", "unknown")

    return {
        "valid": True,
        "assertion": assertion,
        "summary": {
            "assertion_id": badge_id,
            "badge_name": badge_name,
            "issuer_name": issuer_name,
            "recipient_name": assertion.get("recipient", {}).get("name", "unknown"),
            "issued_on": assertion.get("issuedOn"),
        },
    }


JsonFetcher = Callable[[str], dict[str, Any]]


def _default_fetch_json(url: str) -> dict[str, Any]:
    """Charge un document JSON distant avec validation TLS active."""
    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        response = client.get(url, headers={"Accept": "application/ld+json, application/json;q=0.9, */*;q=0.1"})
        response.raise_for_status()
        return response.json()


def _as_url(value: Any) -> str | None:
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return value
    if isinstance(value, dict):
        candidate = value.get("id") or value.get("url")
        if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
            return candidate
    return None


def _hosted_assertion_url(assertion: dict[str, Any]) -> str | None:
    verification = assertion.get("verification")
    if isinstance(verification, dict):
        url = _as_url(verification.get("url"))
        if url:
            return url
    return _as_url(assertion.get("id")) or _as_url(assertion.get("url"))


def _compare_assertions(embedded: dict[str, Any], hosted: dict[str, Any]) -> dict[str, Any]:
    """Compare les champs stables importants d'une assertion baked et hosted."""
    fields = ["id", "type", "badge", "issuer", "issuedOn", "expires"]
    mismatches = []
    for field in fields:
        if embedded.get(field) != hosted.get(field):
            mismatches.append(
                {
                    "field": field,
                    "embedded": embedded.get(field),
                    "hosted": hosted.get(field),
                }
            )

    embedded_recipient = embedded.get("recipient") if isinstance(embedded.get("recipient"), dict) else {}
    hosted_recipient = hosted.get("recipient") if isinstance(hosted.get("recipient"), dict) else {}
    for field in ["type", "hashed", "salt", "identity"]:
        if embedded_recipient.get(field) != hosted_recipient.get(field):
            mismatches.append(
                {
                    "field": f"recipient.{field}",
                    "embedded": embedded_recipient.get(field),
                    "hosted": hosted_recipient.get(field),
                }
            )

    return {"matches": not mismatches, "mismatches": mismatches}


def _fetch_document(url: str | None, fetch_json: JsonFetcher) -> dict[str, Any]:
    if not url:
        return {"url": None, "ok": False, "error": "URL absente", "document": None}
    try:
        document = fetch_json(url)
    except Exception as exc:  # pragma: no cover - exact exception type depends on network layer
        return {"url": url, "ok": False, "error": str(exc), "document": None}
    return {"url": url, "ok": True, "error": None, "document": document}


def deep_verify_baked_badge(png_data: bytes, fetch_json: JsonFetcher | None = None) -> dict[str, Any]:
    """Vérifie un PNG baked et la chaîne HostedBadge associée.

    Cette vérification est inspirée du flux minimal observé dans ``obi-sample`` :
    extraction de l'assertion depuis le chunk ``openbadges``, récupération de
    l'assertion hébergée, puis résolution de BadgeClass et Issuer.
    """
    basic = verify_baked_badge(png_data)
    if not basic.get("valid"):
        return {**basic, "deep": {"ok": False, "checks": []}}

    fetch_json = fetch_json or _default_fetch_json
    embedded_assertion = basic["assertion"]

    assertion_url = _hosted_assertion_url(embedded_assertion)
    hosted_result = _fetch_document(assertion_url, fetch_json)
    checks: list[dict[str, Any]] = [
        {
            "name": "embedded_assertion",
            "ok": True,
            "message": "Assertion Open Badges extraite du PNG.",
        },
        {
            "name": "hosted_assertion_fetch",
            "ok": hosted_result["ok"],
            "url": hosted_result["url"],
            "error": hosted_result["error"],
        },
    ]

    hosted_assertion = hosted_result.get("document") if hosted_result.get("ok") else None
    comparison = {"matches": False, "mismatches": [{"field": "hosted", "error": "Assertion hébergée indisponible"}]}
    badge_result = {"url": None, "ok": False, "error": "Assertion hébergée indisponible", "document": None}
    issuer_result = {"url": None, "ok": False, "error": "BadgeClass indisponible", "document": None}

    if isinstance(hosted_assertion, dict):
        comparison = _compare_assertions(embedded_assertion, hosted_assertion)
        checks.append(
            {
                "name": "hosted_assertion_matches_embedded",
                "ok": comparison["matches"],
                "mismatches": comparison["mismatches"],
            }
        )

        badge_url = _as_url(hosted_assertion.get("badge"))
        badge_result = _fetch_document(badge_url, fetch_json)
        checks.append(
            {
                "name": "badgeclass_fetch",
                "ok": badge_result["ok"],
                "url": badge_result["url"],
                "error": badge_result["error"],
            }
        )

        badge_document = badge_result.get("document") if badge_result.get("ok") else None
        if isinstance(badge_document, dict):
            issuer_url = _as_url(badge_document.get("issuer")) or _as_url(hosted_assertion.get("issuer"))
            issuer_result = _fetch_document(issuer_url, fetch_json)
            checks.append(
                {
                    "name": "issuer_fetch",
                    "ok": issuer_result["ok"],
                    "url": issuer_result["url"],
                    "error": issuer_result["error"],
                }
            )

    deep_ok = all(check.get("ok") for check in checks)
    return {
        **basic,
        "deep": {
            "ok": deep_ok,
            "assertion_url": assertion_url,
            "comparison": comparison,
            "hosted_assertion": hosted_result,
            "badgeclass": badge_result,
            "issuer": issuer_result,
            "checks": checks,
        },
    }
