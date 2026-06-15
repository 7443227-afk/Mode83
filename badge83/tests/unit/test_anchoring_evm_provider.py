from __future__ import annotations

import sys
import types
from unittest.mock import patch

from app.proofs.anchoring_providers import EvmAnchoringProvider, get_anchoring_provider


VALID_HASH = "sha256:" + "ab" * 32


def _configure_evm(monkeypatch) -> None:
    monkeypatch.setenv("BADGE83_EVM_RPC_URL", "http://127.0.0.1:8545")
    monkeypatch.setenv("BADGE83_EVM_CHAIN_ID", "31337")
    monkeypatch.setenv("BADGE83_EVM_CONTRACT_ADDRESS", "0x0000000000000000000000000000000000000001")
    monkeypatch.setenv("BADGE83_EVM_PRIVATE_KEY", "0x" + "11" * 32)
    monkeypatch.setenv("BADGE83_EVM_NETWORK_LABEL", "hardhat-unit")
    monkeypatch.setenv("BADGE83_EVM_CONFIRMATION_TIMEOUT_SECONDS", "30")


def test_provider_evm_selectionnable(monkeypatch):
    monkeypatch.setenv("BADGE83_EVM_NETWORK_LABEL", "hardhat-unit")

    provider = get_anchoring_provider("evm")

    assert isinstance(provider, EvmAnchoringProvider)
    assert provider.name == "evm"
    assert provider.network == "hardhat-unit"


def test_evm_configuration_absente_retourne_failed(monkeypatch):
    monkeypatch.delenv("BADGE83_EVM_RPC_URL", raising=False)
    monkeypatch.delenv("BADGE83_EVM_CONTRACT_ADDRESS", raising=False)
    monkeypatch.delenv("BADGE83_EVM_PRIVATE_KEY", raising=False)

    result = EvmAnchoringProvider().anchor({"credential_hash": VALID_HASH})

    assert result.status == "failed"
    assert "Configuration EVM incomplète" in str(result.error_message)


def test_evm_hash_invalide_retourne_failed(monkeypatch):
    _configure_evm(monkeypatch)

    result = EvmAnchoringProvider().anchor({"credential_hash": "sha256:not-hex"})

    assert result.status == "failed"
    assert "Hash credential invalide" in str(result.error_message)


def test_evm_web3_absent_retourne_failed(monkeypatch):
    _configure_evm(monkeypatch)
    monkeypatch.delitem(sys.modules, "web3", raising=False)

    with patch("app.proofs.anchoring_providers.importlib.import_module", side_effect=ImportError):
        result = EvmAnchoringProvider().anchor({"credential_hash": VALID_HASH})

    assert result.status == "failed"
    assert "web3" in str(result.error_message)


def test_evm_web3_mocke_retourne_anchored_et_bytes32(monkeypatch):
    _configure_evm(monkeypatch)
    recorder: dict[str, object] = {}
    fake_web3_module = _fake_web3_module(recorder)
    monkeypatch.setitem(sys.modules, "web3", fake_web3_module)

    result = EvmAnchoringProvider().anchor(
        {
            "id": 42,
            "assertion_id": "assertion-ne-doit-pas-partir-on-chain",
            "credential_hash": VALID_HASH,
            "canonical_payload": '{"name":"Alice","email":"alice@example.test"}',
            "admin_recipient": {"name": "Alice", "email": "alice@example.test"},
        }
    )

    assert result.status == "anchored"
    assert result.tx_hash == "0x1234"
    assert result.block_number == 123
    assert result.network == "hardhat-unit"
    assert recorder["digest"] == bytes.fromhex("ab" * 32)
    assert recorder["tx_params"] == {
        "from": "0xAccount",
        "nonce": 7,
        "chainId": 31337,
    }


def test_evm_ne_transmet_aucune_donnee_personnelle(monkeypatch):
    _configure_evm(monkeypatch)
    recorder: dict[str, object] = {}
    fake_web3_module = _fake_web3_module(recorder)
    monkeypatch.setitem(sys.modules, "web3", fake_web3_module)

    EvmAnchoringProvider().anchor(
        {
            "credential_hash": VALID_HASH,
            "assertion_id": "assertion-personnelle",
            "canonical_payload": '{"name":"Alice","email":"alice@example.test"}',
            "admin_recipient": {"name": "Alice", "email": "alice@example.test"},
        }
    )

    contract_calls = recorder["contract_calls"]
    assert contract_calls == [bytes.fromhex("ab" * 32)]
    assert "assertion-personnelle" not in repr(contract_calls)
    assert "alice@example.test" not in repr(contract_calls)
    assert "Alice" not in repr(contract_calls)


def test_evm_verification_hash_ancre_read_only(monkeypatch):
    _configure_evm(monkeypatch)
    recorder: dict[str, object] = {"anchored_result": True}
    fake_web3_module = _fake_web3_module(recorder)
    monkeypatch.setitem(sys.modules, "web3", fake_web3_module)

    result = EvmAnchoringProvider().verifier_hash_ancre(VALID_HASH)

    assert result["available"] is True
    assert result["verified"] is True
    assert result["status"] == "verified"
    assert result["provider"] == "evm"
    assert recorder["anchored_digest"] == bytes.fromhex("ab" * 32)
    assert "private_key_used" not in recorder


def test_evm_verification_sans_configuration_ne_demande_pas_de_cle_privee(monkeypatch):
    monkeypatch.setenv("BADGE83_EVM_NETWORK_LABEL", "hardhat-unit")
    monkeypatch.delenv("BADGE83_EVM_RPC_URL", raising=False)
    monkeypatch.delenv("BADGE83_EVM_CONTRACT_ADDRESS", raising=False)
    monkeypatch.setenv("BADGE83_EVM_PRIVATE_KEY", "0x" + "11" * 32)

    result = EvmAnchoringProvider().verifier_hash_ancre(VALID_HASH)

    assert result["available"] is False
    assert result["verified"] is False
    assert result["status"] == "configuration_incomplete"


def _fake_web3_module(recorder: dict[str, object]):
    class FakeAccount:
        address = "0xAccount"

    class FakeSignedTransaction:
        raw_transaction = b"raw-tx"

    class FakeEthAccount:
        @staticmethod
        def from_key(private_key: str):
            recorder["private_key_used"] = private_key
            return FakeAccount()

        @staticmethod
        def sign_transaction(built_tx: dict, private_key: str):
            recorder["signed_tx"] = built_tx
            recorder["signed_with_private_key"] = private_key
            return FakeSignedTransaction()

    class FakeAnchorFunction:
        def __init__(self, digest: bytes) -> None:
            self.digest = digest

        def build_transaction(self, tx_params: dict):
            recorder["digest"] = self.digest
            recorder["tx_params"] = tx_params
            return {"to": "0xContract", "data": self.digest.hex(), **tx_params}

    class FakeAnchoredFunction:
        def __init__(self, digest: bytes) -> None:
            self.digest = digest

        def call(self):
            recorder["anchored_digest"] = self.digest
            return recorder.get("anchored_result", False)

    class FakeFunctions:
        def anchor(self, credential_hash: bytes):
            recorder.setdefault("contract_calls", []).append(credential_hash)
            return FakeAnchorFunction(credential_hash)

        def anchored(self, credential_hash: bytes):
            recorder.setdefault("contract_read_calls", []).append(credential_hash)
            return FakeAnchoredFunction(credential_hash)

    class FakeContract:
        functions = FakeFunctions()

    class FakeEth:
        account = FakeEthAccount()

        @staticmethod
        def contract(address: str, abi: list):
            recorder["contract_address"] = address
            recorder["contract_abi"] = abi
            return FakeContract()

        @staticmethod
        def get_transaction_count(address: str):
            recorder["nonce_for"] = address
            return 7

        @staticmethod
        def send_raw_transaction(raw_tx: bytes):
            recorder["raw_tx"] = raw_tx
            return b"\x12\x34"

        @staticmethod
        def wait_for_transaction_receipt(tx_hash: bytes, timeout: int):
            recorder["waited_for"] = tx_hash
            recorder["timeout"] = timeout
            return {"blockNumber": 123}

    class FakeWeb3:
        eth = FakeEth()

        def __init__(self, provider: object) -> None:
            recorder["provider"] = provider

        @staticmethod
        def HTTPProvider(rpc_url: str):
            recorder["rpc_url"] = rpc_url
            return {"rpc_url": rpc_url}

        @staticmethod
        def to_checksum_address(address: str):
            recorder["checksum_input"] = address
            return "0xContract"

        def is_connected(self):
            return True

    return types.SimpleNamespace(Web3=FakeWeb3)