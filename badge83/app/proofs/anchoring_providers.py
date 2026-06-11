from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AnchoringProviderResult:
    """Résultat normalisé retourné par un provider d'ancrage."""

    status: str
    tx_hash: str | None = None
    block_number: int | None = None
    error_message: str | None = None
    network: str | None = None


class AnchoringProvider(Protocol):
    name: str
    network: str | None

    def anchor(self, transaction: dict) -> AnchoringProviderResult:
        """Ancre une transaction ou retourne un résultat contrôlé."""


class NoopAnchoringProvider:
    """Provider désactivé : aucune écriture externe n'est effectuée."""

    name = "noop"
    network = None

    def anchor(self, transaction: dict) -> AnchoringProviderResult:
        return AnchoringProviderResult(
            status="failed",
            error_message="Aucun provider d'ancrage réel n'est configuré.",
            network=self.network,
        )


class MockAnchoringProvider:
    """Provider de démonstration : simule un ancrage réussi sans réseau."""

    name = "mock"
    network = "local-demo"

    def anchor(self, transaction: dict) -> AnchoringProviderResult:
        credential_hash = str(transaction.get("credential_hash") or "")
        suffix = credential_hash.replace("sha256:", "").replace("sha256$", "")[:16] or str(transaction.get("id"))
        return AnchoringProviderResult(
            status="anchored",
            tx_hash=f"mock:{suffix}",
            block_number=int(transaction.get("id") or 1),
            network=self.network,
        )


def get_anchoring_provider(name: str | None) -> AnchoringProvider:
    provider_name = (name or "noop").strip().lower()
    if provider_name == "mock":
        return MockAnchoringProvider()
    return NoopAnchoringProvider()