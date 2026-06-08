from __future__ import annotations

import hashlib
from typing import Any

from app.proofs.canonical import CanonicalCredentialService


ALGORITHME_HASH = "sha256"


class HashService:
    """Calcule le hash déterministe d'une assertion Badge83."""

    hash_algorithm = ALGORITHME_HASH

    prefixe_hash = "sha256:"


    def __init__(self, canonical_service: CanonicalCredentialService | None = None) -> None:
        self.canonical_service = canonical_service or CanonicalCredentialService()

    def calculer_hash(self, assertion: dict[str, Any]) -> str:
        """Retourne le hash SHA-256 préfixé de l'assertion canonique."""

        payload_canonique = self.canonical_service.serialiser(assertion)
        digest = hashlib.sha256(payload_canonique.encode("utf-8")).hexdigest()
        return f"{self.prefixe_hash}{digest}"

    def construire_payload_canonique(self, assertion: dict[str, Any]) -> str:
        """Expose le payload canonique utilisé pour le calcul du hash."""

        return self.canonical_service.serialiser(assertion)