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
    is_valid_evm_address,
)


SHA256_CREDENTIAL_HASH_RE = re.compile(r"^sha256:([0-9a-fA-F]{64})$")

BADGE83_ANCHOR_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "credentialHash", "type": "bytes32"}],
        "name": "anchor",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "credentialHash", "type": "bytes32"}],
        "name": "revoke",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "name": "anchored",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "name": "revoked",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "credentialHash", "type": "bytes32"}],
        "name": "getStatus",
        "outputs": [
            {"internalType": "bool", "name": "isHashAnchored", "type": "bool"},
            {"internalType": "bool", "name": "isHashRevoked", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
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

    def revoke(self, transaction: dict) -> AnchoringProviderResult:
        return AnchoringProviderResult(
            status="not_configured",
            error_message="Aucun provider de révocation blockchain réel n'est configuré.",
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

    def revoke(self, transaction: dict) -> AnchoringProviderResult:
        credential_hash = str(transaction.get("credential_hash") or "")
        suffix = credential_hash.replace("sha256:", "").replace("sha256$", "")[:16] or str(transaction.get("id"))
        return AnchoringProviderResult(
            status="revoked",
            tx_hash=f"mock-revoke:{suffix}",
            block_number=int(transaction.get("id") or 1),
            network=self.network,
        )


class EvmAnchoringProvider:
    """Provider EVM optionnel : ancre uniquement le digest SHA-256 opaque."""

    name = "evm"

    def __init__(self) -> None:
        self.network = get_evm_network_label()

    def anchor(self, transaction: dict) -> AnchoringProviderResult:
        return self._send_transaction(transaction, function_name="anchor", success_status="anchored", error_prefix="Erreur ancrage EVM")

    def revoke(self, transaction: dict) -> AnchoringProviderResult:
        return self._send_transaction(transaction, function_name="revoke", success_status="revoked", error_prefix="Erreur révocation EVM")

    def verifier_hash_ancre(self, credential_hash: str) -> dict[str, object]:
        """Vérifie en lecture seule si le digest est marqué comme ancré on-chain."""

        digest_match = SHA256_CREDENTIAL_HASH_RE.match(str(credential_hash or ""))
        if not digest_match:
            return self._verification_result(
                available=False,
                verified=False,
                status="invalid_hash",
                error_message="Hash credential invalide : format sha256:<64 hex> attendu.",
            )

        rpc_url = get_evm_rpc_url()
        contract_address = get_evm_contract_address()
        if not rpc_url or not contract_address:
            return self._verification_result(
                available=False,
                verified=False,
                status="configuration_incomplete",
                error_message="Configuration EVM de vérification incomplète.",
            )
        if not is_valid_evm_address(contract_address):
            return self._verification_result(
                available=False,
                verified=False,
                status="invalid_contract_address",
                error_message="Adresse de contrat EVM invalide.",
            )

        try:
            web3_module = importlib.import_module("web3")
        except ImportError:
            return self._verification_result(
                available=False,
                verified=False,
                status="dependency_missing",
                error_message="Dépendance optionnelle web3 non installée.",
            )

        try:
            web3_class = web3_module.Web3
            w3 = web3_class(web3_class.HTTPProvider(rpc_url))
            if hasattr(w3, "is_connected") and not w3.is_connected():
                return self._verification_result(
                    available=False,
                    verified=False,
                    status="rpc_unavailable",
                    error_message="RPC EVM indisponible.",
                )

            checksum_address = web3_class.to_checksum_address(contract_address)
            contract = w3.eth.contract(address=checksum_address, abi=BADGE83_ANCHOR_ABI)
            digest_bytes = bytes.fromhex(digest_match.group(1))
            is_anchored = bool(contract.functions.anchored(digest_bytes).call())
            return self._verification_result(
                available=True,
                verified=is_anchored,
                status="verified" if is_anchored else "not_found_on_chain",
            )
        except Exception as exc:
            return self._verification_result(
                available=False,
                verified=False,
                status="verification_failed",
                error_message=f"Erreur vérification EVM : {exc}",
            )

    def verifier_hash_revoque(self, credential_hash: str) -> dict[str, object]:
        """Vérifie en lecture seule si le digest est marqué comme révoqué on-chain."""

        status = self.get_hash_status(credential_hash)
        if status.get("available") is not True:
            return {
                **status,
                "verified": False,
                "revoked": False,
            }
        revoked = bool(status.get("revoked"))
        return {
            **status,
            "verified": revoked,
            "status": "revoked" if revoked else "not_revoked_on_chain",
        }

    def get_hash_status(self, credential_hash: str) -> dict[str, object]:
        """Lit getStatus(bytes32) si disponible, sans transaction ni clé privée."""

        read_context = self._prepare_read_context(credential_hash, private_key_required=False)
        if "error" in read_context:
            return read_context["error"]

        try:
            contract = read_context["contract"]
            digest_bytes = read_context["digest_bytes"]
            anchored, revoked = contract.functions.getStatus(digest_bytes).call()
            return self._status_result(
                available=True,
                anchored=bool(anchored),
                revoked=bool(revoked),
                status="revoked" if revoked else "anchored" if anchored else "not_found_on_chain",
            )
        except Exception as exc:
            return self._status_result(
                available=False,
                anchored=False,
                revoked=False,
                status="status_failed",
                error_message=f"Erreur statut EVM : {exc}",
            )

    def _send_transaction(
        self,
        transaction: dict,
        *,
        function_name: str,
        success_status: str,
        error_prefix: str,
    ) -> AnchoringProviderResult:
        read_context = self._prepare_read_context(str(transaction.get("credential_hash") or ""), private_key_required=True)
        if "error_message" in read_context:
            error_status = str(read_context.get("status") or "failed") if function_name == "revoke" else "failed"
            return self._failed(str(read_context["error_message"]), status=error_status)

        try:
            w3 = read_context["w3"]
            contract = read_context["contract"]
            digest_bytes = read_context["digest_bytes"]
            private_key = read_context["private_key"]
            account = w3.eth.account.from_key(private_key)
            tx_params = {
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
            }
            chain_id = get_evm_chain_id()
            if chain_id is not None:
                tx_params["chainId"] = chain_id

            contract_function = getattr(contract.functions, function_name)(digest_bytes)
            built_tx = contract_function.build_transaction(tx_params)
            signed_tx = w3.eth.account.sign_transaction(built_tx, private_key=private_key)
            raw_tx = getattr(signed_tx, "rawTransaction", None) or getattr(signed_tx, "raw_transaction")
            tx_hash = w3.eth.send_raw_transaction(raw_tx)
            receipt = w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=get_evm_confirmation_timeout_seconds(),
            )
            block_number = self._receipt_get(receipt, "blockNumber")
            return AnchoringProviderResult(
                status=success_status,
                tx_hash=self._to_hex(w3, tx_hash),
                block_number=int(block_number) if block_number is not None else None,
                network=self.network,
            )
        except Exception as exc:
            return self._failed(f"{error_prefix} : {exc}")

    def _prepare_read_context(self, credential_hash: str, *, private_key_required: bool) -> dict[str, object]:
        digest_match = SHA256_CREDENTIAL_HASH_RE.match(str(credential_hash or ""))
        if not digest_match:
            return self._context_error(
                "invalid_hash",
                "Hash credential invalide : format sha256:<64 hex> attendu.",
                private_key_required=private_key_required,
            )

        rpc_url = get_evm_rpc_url()
        contract_address = get_evm_contract_address()
        private_key = get_evm_private_key() if private_key_required else None
        if not rpc_url or not contract_address or (private_key_required and not private_key):
            return self._context_error(
                "not_configured" if private_key_required else "configuration_incomplete",
                "Configuration EVM incomplète.",
                private_key_required=private_key_required,
            )
        if not is_valid_evm_address(contract_address):
            return self._context_error(
                "invalid_contract_address",
                "Adresse de contrat EVM invalide.",
                private_key_required=private_key_required,
            )

        try:
            web3_module = importlib.import_module("web3")
        except ImportError:
            return self._context_error(
                "dependency_missing",
                "Dépendance optionnelle web3 non installée.",
                private_key_required=private_key_required,
            )

        try:
            web3_class = web3_module.Web3
            w3 = web3_class(web3_class.HTTPProvider(rpc_url))
            if hasattr(w3, "is_connected") and not w3.is_connected():
                return self._context_error(
                    "rpc_unavailable",
                    "RPC EVM indisponible.",
                    private_key_required=private_key_required,
                )

            checksum_address = web3_class.to_checksum_address(contract_address)
            contract = w3.eth.contract(address=checksum_address, abi=BADGE83_ANCHOR_ABI)
            return {
                "w3": w3,
                "contract": contract,
                "digest_bytes": bytes.fromhex(digest_match.group(1)),
                "private_key": private_key,
            }
        except Exception as exc:
            return self._context_error(
                "configuration_failed",
                f"Erreur configuration EVM : {exc}",
                private_key_required=private_key_required,
            )

    def _context_error(self, status: str, message: str, *, private_key_required: bool) -> dict[str, object]:
        if private_key_required:
            return {"status": status, "error_message": message}
        return {
            "error": self._status_result(
                available=False,
                anchored=False,
                revoked=False,
                status=status,
                error_message=message,
            )
        }

    def _failed(self, message: str, *, status: str = "failed") -> AnchoringProviderResult:
        return AnchoringProviderResult(status=status, error_message=message, network=self.network)

    def _status_result(
        self,
        *,
        available: bool,
        anchored: bool,
        revoked: bool,
        status: str,
        error_message: str | None = None,
    ) -> dict[str, object]:
        return {
            "available": available,
            "anchored": anchored,
            "revoked": revoked,
            "status": status,
            "provider": self.name,
            "network": self.network,
            "error_message": error_message,
        }

    def _verification_result(
        self,
        *,
        available: bool,
        verified: bool,
        status: str,
        error_message: str | None = None,
    ) -> dict[str, object]:
        return {
            "available": available,
            "verified": verified,
            "status": status,
            "provider": self.name,
            "network": self.network,
            "error_message": error_message,
        }

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