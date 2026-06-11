from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


STATUTS_ANCRAGE_AUTORISES = {
    "queued",
    "pending",
    "anchored",
    "failed",
    "retry_scheduled",
}


def _maintenant_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normaliser_statut_ancrage(status: str | None) -> str:
    valeur = (status or "queued").strip().lower()
    if valeur not in STATUTS_ANCRAGE_AUTORISES:
        return "queued"
    return valeur


@dataclass(frozen=True)
class AnchoringTransaction:
    """Demande locale d'ancrage d'un hash credential."""

    assertion_id: str
    credential_hash: str
    provider: str = "noop"
    network: str | None = None
    status: str = "queued"
    tx_hash: str | None = None
    block_number: int | None = None
    error_message: str | None = None
    attempts: int = 0
    next_retry_at: str | None = None
    created_at: str = field(default_factory=_maintenant_iso)
    updated_at: str = field(default_factory=_maintenant_iso)

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", normaliser_statut_ancrage(self.status))
