from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


VERSION_PREUVE = "badge83-proof-v1"
STATUT_ANCRAGE_PAR_DEFAUT = "not_requested"


@dataclass(frozen=True)
class VerificationProof:
    """Preuve locale associée à une assertion Badge83."""

    assertion_id: str
    credential_hash: str
    canonical_payload: str
    proof_version: str = VERSION_PREUVE
    hash_algorithm: str = "sha256"
    canonicalization: str = "json-rfc8785-lite-v1"
    anchoring_status: str = STATUT_ANCRAGE_PAR_DEFAUT
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            object.__setattr__(
                self,
                "created_at",
                datetime.now(timezone.utc).isoformat(),
            )

    def to_dict(self) -> dict[str, str]:
        """Retourne une représentation sérialisable de la preuve."""

        return {
            "assertion_id": self.assertion_id,
            "proof_version": self.proof_version,
            "hash_algorithm": self.hash_algorithm,
            "canonicalization": self.canonicalization,
            "credential_hash": self.credential_hash,
            "canonical_payload": self.canonical_payload,
            "anchoring_status": self.anchoring_status,
            "created_at": self.created_at,
        }