from __future__ import annotations

from app.openbadges_checks import check_assertion, check_badgeclass, check_issuer, check_openbadges_chain


SHA256_IDENTITY = "sha256$" + "a" * 64


def _valid_assertion() -> dict:
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "id": "https://tests.mode83.local/assertions/123",
        "type": "Assertion",
        "badge": "https://tests.mode83.local/badges/blockchain-foundations",
        "issuer": "https://tests.mode83.local/issuers/main",
        "issuedOn": "2026-05-28T10:00:00+00:00",
        "recipient": {
            "type": "email",
            "hashed": True,
            "salt": "abc",
            "identity": SHA256_IDENTITY,
        },
        "verification": {
            "type": "HostedBadge",
            "url": "https://tests.mode83.local/assertions/123",
        },
    }


def _valid_badgeclass() -> dict:
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "id": "https://tests.mode83.local/badges/blockchain-foundations",
        "type": "BadgeClass",
        "name": "MODE83 Fondamentaux Blockchain",
        "description": "Badge de validation.",
        "image": "https://tests.mode83.local/assets/mode83-badge.png",
        "criteria": {"narrative": "Validation du parcours."},
        "issuer": "https://tests.mode83.local/issuers/main",
    }


def _valid_issuer() -> dict:
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "id": "https://tests.mode83.local/issuers/main",
        "type": "Issuer",
        "name": "MODE83",
        "url": "https://tests.mode83.local",
        "verification": {
            "type": "VerificationObject",
            "allowedOrigins": ["tests.mode83.local"],
            "startsWith": ["https://tests.mode83.local/assertions/"],
        },
    }


def test_check_assertion_returns_structured_valid_report():
    report = check_assertion(_valid_assertion())

    assert report["valid"] is True
    assert report["errorCount"] == 0
    assert report["warningCount"] == 0
    assert report["messages"] == []
    assert {check["name"] for check in report["checks"]} >= {
        "assertion.context",
        "assertion.type",
        "recipient.identity",
        "verification.type",
    }


def test_check_assertion_reports_missing_required_fields():
    assertion = _valid_assertion()
    assertion.pop("@context")
    assertion["recipient"]["identity"] = "plain@example.com"
    assertion["verification"]["type"] = "SignedBadge"

    report = check_assertion(assertion)

    assert report["valid"] is False
    assert report["errorCount"] == 3
    assert "Contexte Open Badges 2.0 présent." in report["messages"]
    assert "Identité au format sha256$... valide." in report["messages"]
    assert "Vérification HostedBadge déclarée." in report["messages"]


def test_check_badgeclass_and_issuer_validate_chain_rules():
    assertion = _valid_assertion()
    badgeclass = _valid_badgeclass()
    issuer = _valid_issuer()

    badge_report = check_badgeclass(badgeclass, assertion)
    issuer_report = check_issuer(issuer, assertion, badgeclass)
    chain_report = check_openbadges_chain(assertion, badgeclass, issuer)

    assert badge_report["valid"] is True
    assert issuer_report["valid"] is True
    assert chain_report["valid"] is True
    assert chain_report["errorCount"] == 0
    assert any(check["name"] == "issuer.allowedOrigins.matches" for check in issuer_report["checks"])
    assert any(check["name"] == "issuer.startsWith.matches" for check in issuer_report["checks"])


def test_check_issuer_reports_allowed_origin_mismatch():
    assertion = _valid_assertion()
    issuer = _valid_issuer()
    issuer["verification"]["allowedOrigins"] = ["other.example"]

    report = check_issuer(issuer, assertion, _valid_badgeclass())

    assert report["valid"] is False
    assert "Origine de l'assertion autorisée par l'émetteur." in report["messages"]