from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


EVENEMENTS_AUDIT_AUTORISES = {
    "credential_issued",
    "proof_created",
    "credential_revoked",
    "anchoring_requested",
    "anchoring_completed",
    "anchoring_failed",
}


def _maintenant_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AuditEvent:
    """Événement de cycle de vie d'un credential Badge83."""

    event_type: str
    actor: str | None = None
    assertion_id: str | None = None
    credential_hash: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=_maintenant_iso)

    def __post_init__(self) -> None:
        if self.event_type not in EVENEMENTS_AUDIT_AUTORISES:
            raise ValueError(f"Type d'événement audit non autorisé: {self.event_type}")
