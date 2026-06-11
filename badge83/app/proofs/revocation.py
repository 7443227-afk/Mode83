from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


RAISONS_REVOCATION_AUTORISEES = {
    "erreur_emission",
    "demande_titulaire",
    "expiration_admin",
    "fraude",
    "autre",
}

RAISON_REVOCATION_PAR_DEFAUT = "autre"


def _maintenant_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normaliser_raison_revocation(reason_category: str | None) -> str:
    """Retourne une catégorie de révocation contrôlée."""

    valeur = (reason_category or RAISON_REVOCATION_PAR_DEFAUT).strip().lower()
    if valeur not in RAISONS_REVOCATION_AUTORISEES:
        return RAISON_REVOCATION_PAR_DEFAUT
    return valeur


@dataclass(frozen=True)
class CredentialRevocation:
    """Révocation locale d'un credential Badge83."""

    assertion_id: str
    reason_category: str = RAISON_REVOCATION_PAR_DEFAUT
    actor: str | None = None
    revoked: bool = True
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        now = _maintenant_iso()
        object.__setattr__(self, "reason_category", normaliser_raison_revocation(self.reason_category))
        if not self.created_at:
            object.__setattr__(self, "created_at", now)
        if not self.updated_at:
            object.__setattr__(self, "updated_at", now)

    def to_dict(self) -> dict[str, str | int | None]:
        """Retourne une représentation adaptée à SQLite."""

        return {
            "assertion_id": self.assertion_id,
            "revoked": 1 if self.revoked else 0,
            "reason_category": self.reason_category,
            "actor": self.actor,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }