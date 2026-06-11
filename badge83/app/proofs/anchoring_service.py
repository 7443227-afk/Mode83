from __future__ import annotations

from pathlib import Path
from typing import Any

from app.proofs.audit import AuditEvent
from app.proofs.audit_repository import AuditRepository
from app.proofs.anchoring_repository import AnchoringRepository
from app.proofs.anchoring_providers import AnchoringProvider, get_anchoring_provider
from app.proofs.repository import ProofRepository


class AnchoringService:
    """Service local d'ancrage : queue + provider + audit."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = db_path
        self.anchoring_repository = AnchoringRepository(db_path)
        self.proof_repository = ProofRepository(db_path)
        self.audit_repository = AuditRepository(db_path)

    def demander_ancrage(
        self,
        assertion_id: str,
        *,
        provider: str = "mock",
        actor: str | None = None,
    ) -> dict[str, Any]:
        proof = self.proof_repository.trouver_par_assertion(assertion_id)
        if not proof:
            raise ValueError("Preuve locale introuvable pour cette assertion.")

        provider_instance = get_anchoring_provider(provider)
        transaction = self.anchoring_repository.enqueue(
            assertion_id=assertion_id,
            credential_hash=proof["credential_hash"],
            provider=provider_instance.name,
            network=provider_instance.network,
        )
        self._auditer(
            "anchoring_requested",
            transaction,
            actor=actor,
            payload={"provider": provider_instance.name, "network": provider_instance.network},
        )
        return transaction

    def traiter_transaction(
        self,
        transaction_id: int,
        *,
        provider: str | AnchoringProvider | None = None,
        actor: str | None = None,
    ) -> dict[str, Any]:
        transaction = self.anchoring_repository.trouver(transaction_id)
        if not transaction:
            raise ValueError("Transaction d'ancrage introuvable.")

        provider_instance = provider if hasattr(provider, "anchor") else get_anchoring_provider(provider or transaction.get("provider"))
        pending = self.anchoring_repository.changer_statut(
            transaction_id,
            "pending",
            increment_attempts=True,
        )
        result = provider_instance.anchor(pending)

        updated = self.anchoring_repository.changer_statut(
            transaction_id,
            result.status,
            tx_hash=result.tx_hash,
            block_number=result.block_number,
            error_message=result.error_message,
        )
        self._auditer(
            "anchoring_completed" if result.status == "anchored" else "anchoring_failed",
            updated,
            actor=actor,
            payload={
                "provider": getattr(provider_instance, "name", updated.get("provider")),
                "network": result.network or updated.get("network"),
                "status": result.status,
                "tx_hash": result.tx_hash,
                "error_message": result.error_message,
            },
        )
        return updated

    def traiter_file(
        self,
        *,
        provider: str = "mock",
        limit: int = 10,
        actor: str | None = None,
    ) -> list[dict[str, Any]]:
        queued = self.anchoring_repository.lister_par_statut("queued")[:limit]
        return [
            self.traiter_transaction(transaction["id"], provider=provider, actor=actor)
            for transaction in queued
        ]

    def _auditer(
        self,
        event_type: str,
        transaction: dict[str, Any],
        *,
        actor: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.audit_repository.enregistrer(
            AuditEvent(
                event_type=event_type,
                actor=actor,
                assertion_id=transaction.get("assertion_id"),
                credential_hash=transaction.get("credential_hash"),
                payload=payload or {},
            )
        )


def demander_ancrage(assertion_id: str, *, provider: str = "mock", actor: str | None = None) -> dict[str, Any]:
    return AnchoringService().demander_ancrage(assertion_id, provider=provider, actor=actor)