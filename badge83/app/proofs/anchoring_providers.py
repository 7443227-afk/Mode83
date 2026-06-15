from __future__ import annotations

from dataclasses import dataclass
import importlib
import re
from typing import Protocol

from app.config import (
    get_evm_chain_id,
    get_evm_confirmation_timeout_seconds,
    get_evm_contract_address,
    get_evm_network_label,
    get_evm_private_key,
    get_evm_rpc_url,
)


SHA256_CREDENTIAL_HASH_RE = re.compile(r"^sha256:([0-9a-fA-F]{64})$")

BADGE83_ANCHOR_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "credentialHash", "type": "bytes32"}],
        "name": "anchor",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


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


class EvmAnchoringProvider:
    """Provider EVM optionnel : ancre uniquement le digest SHA-256 opaque."""

    name = "evm"

    def __init__(self) -> None:
        self.network = get_evm_network_label()

    def anchor(self, transaction: dict) -> AnchoringProviderResult:
        credential_hash = str(transaction.get("credential_hash") or "")
        digest_match = SHA256_CREDENTIAL_HASH_RE.match(credential_hash)
        if not digest_match:
            return self._failed("Hash credential invalide : format sha256:<64 hex> attendu.")

        rpc_url = get_evm_rpc_url()
        contract_address = get_evm_contract_address()
        private_key = get_evm_private_key()
        if not rpc_url or not contract_address or not private_key:
            return self._failed("Configuration EVM incomplète.")

        try:
            web3_module = importlib.import_module("web3")
        except ImportError:
            return self._failed("Dépendance optionnelle web3 non installée.")

        try:
            web3_class = web3_module.Web3
            w3 = web3_class(web3_class.HTTPProvider(rpc_url))
            if hasattr(w3, "is_connected") and not w3.is_connected():
                return self._failed("RPC EVM indisponible.")

            account = w3.eth.account.from_key(private_key)
            checksum_address = web3_class.to_checksum_address(contract_address)
            contract = w3.eth.contract(address=checksum_address, abi=BADGE83_ANCHOR_ABI)
            digest_bytes = bytes.fromhex(digest_match.group(1))
            tx_params = {
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
            }
            chain_id = get_evm_chain_id()
            if chain_id is not None:
                tx_params["chainId"] = chain_id

            built_tx = contract.functions.anchor(digest_bytes).build_transaction(tx_params)
            signed_tx = w3.eth.account.sign_transaction(built_tx, private_key=private_key)
            raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction")
            tx_hash = w3.eth.send_raw_transaction(raw_tx)
            receipt = w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=get_evm_confirmation_timeout_seconds(),
            )
            block_number = self._receipt_get(receipt, "blockNumber")
            return AnchoringProviderResult(
                status="anchored",
                tx_hash=self._to_hex(w3, tx_hash),
                block_number=int(block_number) if block_number is not None else None,
                network=self.network,
            )
        except Exception as exc:
            return self._failed(f"Erreur ancrage EVM : {exc}")

    def _failed(self, message: str) -> AnchoringProviderResult:
        return AnchoringProviderResult(status="failed", error_message=message, network=self.network)

    @staticmethod
    def _receipt_get(receipt: object, key: str) -> object | None:
        if isinstance(receipt, dict):
            return receipt.get(key)
        return getattr(receipt, key, None)

    @staticmethod
    def _to_hex(w3: object, value: object) -> str:
        if isinstance(value, bytes):
            return "0x" + value.hex()
        if hasattr(value, "hex"):
            return value.hex()  # type: ignore[no-any-return]
        return w3.to_hex(value)  # type: ignore[attr-defined,no-any-return]


def get_anchoring_provider(name: str | None) -> AnchoringProvider:
    provider_name = (name or "noop").strip().lower()
    if provider_name == "mock":
        return MockAnchoringProvider()
    if provider_name == "evm":
        return EvmAnchoringProvider()
    return NoopAnchoringProvider()