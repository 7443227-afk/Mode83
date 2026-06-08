from __future__ import annotations

import copy
import json

from app.proofs import CanonicalCredentialService, HashService, VerificationProof


def construire_assertion_exemple() -> dict:
    return {
        "@context": "https://w3id.org/openbadges/v2",
        "id": "https://tests.mode83.local/assertions/assertion-1",
        "type": "Assertion",
        "recipient": {
            "type": "email",
            "hashed": True,
            "salt": "sel-test",
            "identity": "sha256$abc123",
        },
        "badge": "https://tests.mode83.local/badges/blockchain-foundations",
        "issuer": "https://tests.mode83.local/issuers/main",
        "issuedOn": "2026-06-08T10:00:00+00:00",
        "expires": "2027-06-08T10:00:00+00:00",
        "verification": {
            "type": "HostedBadge",
            "url": "https://tests.mode83.local/assertions/assertion-1",
        },
        "field_values": {
            "formation": "Fondamentaux Blockchain",
            "niveau": "initial",
        },
        "badge83_template": {
            "id": "template-1",
            "name": "Modèle standard",
        },
        "admin_recipient": {
            "name": "Alice Exemple",
            "email": "alice@example.com",
        },
        "search": {
            "name_hash": "sha256$nom",
            "email_hash": "sha256$email",
        },
    }


def test_meme_assertion_produit_le_meme_hash():
    service = HashService()
    assertion = construire_assertion_exemple()

    assert service.calculer_hash(assertion) == service.calculer_hash(assertion)


def test_ordre_des_cles_json_ne_change_pas_le_hash():
    service = HashService()
    assertion = construire_assertion_exemple()
    assertion_reordonnee = json.loads(json.dumps(assertion, sort_keys=True))

    assert service.calculer_hash(assertion) == service.calculer_hash(assertion_reordonnee)


def test_admin_recipient_ne_change_pas_le_hash():
    service = HashService()
    assertion = construire_assertion_exemple()
    assertion_modifiee = copy.deepcopy(assertion)
    assertion_modifiee["admin_recipient"] = {
        "name": "Alice Modifiée",
        "email": "autre@example.com",
    }

    assert service.calculer_hash(assertion) == service.calculer_hash(assertion_modifiee)


def test_metadonnees_search_ne_changent_pas_le_hash():
    service = HashService()
    assertion = construire_assertion_exemple()
    assertion_modifiee = copy.deepcopy(assertion)
    assertion_modifiee["search"] = {
        "name_hash": "sha256$autre-nom",
        "email_hash": "sha256$autre-email",
    }

    assert service.calculer_hash(assertion) == service.calculer_hash(assertion_modifiee)


def test_changement_identite_destinataire_change_le_hash():
    service = HashService()
    assertion = construire_assertion_exemple()
    assertion_modifiee = copy.deepcopy(assertion)
    assertion_modifiee["recipient"]["identity"] = "sha256$autre-identite"

    assert service.calculer_hash(assertion) != service.calculer_hash(assertion_modifiee)


def test_changement_date_emission_change_le_hash():
    service = HashService()
    assertion = construire_assertion_exemple()
    assertion_modifiee = copy.deepcopy(assertion)
    assertion_modifiee["issuedOn"] = "2026-06-09T10:00:00+00:00"

    assert service.calculer_hash(assertion) != service.calculer_hash(assertion_modifiee)


def test_payload_canonique_exclut_les_donnees_administratives():
    service = CanonicalCredentialService()
    payload = service.construire_payload(construire_assertion_exemple())

    assert "admin_recipient" not in payload
    assert "search" not in payload
    assert payload["schema_version"] == "openbadges-2.0-badge83"


def test_modele_preuve_est_serialisable():
    hash_service = HashService()
    assertion = construire_assertion_exemple()
    preuve = VerificationProof(
        assertion_id="assertion-1",
        credential_hash=hash_service.calculer_hash(assertion),
        canonical_payload=hash_service.construire_payload_canonique(assertion),
    )

    donnees = preuve.to_dict()

    assert donnees["proof_version"] == "badge83-proof-v1"
    assert donnees["hash_algorithm"] == "sha256"
    assert donnees["canonicalization"] == "json-rfc8785-lite-v1"
    assert donnees["anchoring_status"] == "not_requested"
    assert donnees["credential_hash"].startswith("sha256:")