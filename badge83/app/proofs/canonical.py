from __future__ import annotations

import copy
import json
from typing import Any


CANONICALISATION_VERSION = "json-rfc8785-lite-v1"

CHAMPS_CANONIQUES = (
    "@context",
    "schema_version",
    "id",
    "type",
    "recipient",
    "badge",
    "issuer",
    "issuedOn",
    "expires",
    "verification",
    "field_values",
    "badge83_template",
)


class CanonicalCredentialService:
    """Produit une représentation JSON stable d'une assertion Badge83.

    La représentation canonique exclut volontairement les métadonnées privées
    ou administratives comme ``admin_recipient`` et ``search``. Le résultat est
    destiné au calcul d'un hash local vérifiable et, plus tard, à un ancrage
    blockchain optionnel.
    """

    canonicalisation = CANONICALISATION_VERSION

    def construire_payload(self, assertion: dict[str, Any]) -> dict[str, Any]:
        """Construit le payload canonique à partir d'une assertion."""

        payload: dict[str, Any] = {}
        for champ in CHAMPS_CANONIQUES:
            if champ in assertion and assertion[champ] is not None:
                payload[champ] = copy.deepcopy(assertion[champ])

        payload.setdefault("schema_version", "openbadges-2.0-badge83")
        return payload

    def serialiser(self, assertion: dict[str, Any]) -> str:
        """Sérialise l'assertion en JSON compact avec clés triées."""

        payload = self.construire_payload(assertion)
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )