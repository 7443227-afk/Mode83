from __future__ import annotations

from app import config
import pytest


def test_explicit_base_url_wins_over_internal_port(monkeypatch):
    monkeypatch.setenv("BADGE83_BASE_URL", "https://mode83.ddns.net/")
    monkeypatch.setenv("BADGE83_PORT", "8000")

    assert config.get_public_base_url() == "https://mode83.ddns.net"


def test_default_public_base_url_uses_https_without_internal_port(monkeypatch):
    monkeypatch.delenv("BADGE83_BASE_URL", raising=False)
    monkeypatch.delenv("BADGE83_PUBLIC_SCHEME", raising=False)
    monkeypatch.delenv("BADGE83_PUBLIC_HOST", raising=False)
    monkeypatch.delenv("BADGE83_PUBLIC_PORT", raising=False)
    monkeypatch.setenv("BADGE83_PORT", "8000")

    assert config.get_public_base_url() == "https://mode83.ddns.net"


def test_standard_https_public_port_is_omitted(monkeypatch):
    monkeypatch.delenv("BADGE83_BASE_URL", raising=False)
    monkeypatch.setenv("BADGE83_PUBLIC_SCHEME", "https")
    monkeypatch.setenv("BADGE83_PUBLIC_HOST", "mode83.ddns.net")
    monkeypatch.setenv("BADGE83_PUBLIC_PORT", "443")
    monkeypatch.setenv("BADGE83_PORT", "8000")

    assert config.get_public_base_url() == "https://mode83.ddns.net"


def test_non_standard_public_port_is_preserved(monkeypatch):
    monkeypatch.delenv("BADGE83_BASE_URL", raising=False)
    monkeypatch.setenv("BADGE83_PUBLIC_SCHEME", "https")
    monkeypatch.setenv("BADGE83_PUBLIC_HOST", "mode83.ddns.net")
    monkeypatch.setenv("BADGE83_PUBLIC_PORT", "8443")

    assert config.get_public_base_url() == "https://mode83.ddns.net:8443"


def test_development_env_allows_default_security_values(monkeypatch):
    monkeypatch.delenv("BADGE83_ENV", raising=False)
    monkeypatch.delenv("BADGE83_AUTH_PASSWORD", raising=False)
    monkeypatch.delenv("BADGE83_AUTH_SECRET", raising=False)
    monkeypatch.delenv("BADGE83_SEARCH_PEPPER", raising=False)

    config.validate_production_security_config()


def test_production_env_rejects_default_auth_password(monkeypatch):
    monkeypatch.setenv("BADGE83_ENV", "production")
    monkeypatch.setenv("BADGE83_AUTH_PASSWORD", config.DEFAULT_AUTH_PASSWORD)
    monkeypatch.setenv("BADGE83_AUTH_SECRET", "strong-test-secret")
    monkeypatch.setenv("BADGE83_SEARCH_PEPPER", "strong-test-pepper")

    with pytest.raises(RuntimeError, match="BADGE83_AUTH_PASSWORD"):
        config.validate_production_security_config()


def test_production_env_rejects_default_auth_secret(monkeypatch):
    monkeypatch.setenv("BADGE83_ENV", "production")
    monkeypatch.setenv("BADGE83_AUTH_PASSWORD", "strong-test-password")
    monkeypatch.setenv("BADGE83_AUTH_SECRET", config.DEFAULT_AUTH_SECRET)
    monkeypatch.setenv("BADGE83_SEARCH_PEPPER", "strong-test-pepper")

    with pytest.raises(RuntimeError, match="BADGE83_AUTH_SECRET"):
        config.validate_production_security_config()


def test_production_env_rejects_default_search_pepper(monkeypatch):
    monkeypatch.setenv("BADGE83_ENV", "production")
    monkeypatch.setenv("BADGE83_AUTH_PASSWORD", "strong-test-password")
    monkeypatch.setenv("BADGE83_AUTH_SECRET", "strong-test-secret")
    monkeypatch.setenv("BADGE83_SEARCH_PEPPER", config.DEFAULT_SEARCH_PEPPER)

    with pytest.raises(RuntimeError, match="BADGE83_SEARCH_PEPPER"):
        config.validate_production_security_config()


def test_production_env_accepts_non_default_security_values(monkeypatch):
    monkeypatch.setenv("BADGE83_ENV", "production")
    monkeypatch.setenv("BADGE83_AUTH_PASSWORD", "strong-test-password")
    monkeypatch.setenv("BADGE83_AUTH_SECRET", "strong-test-secret")
    monkeypatch.setenv("BADGE83_SEARCH_PEPPER", "strong-test-pepper")

    config.validate_production_security_config()


def test_upload_limits_can_be_overridden(monkeypatch):
    monkeypatch.setenv("BADGE83_MAX_PNG_UPLOAD_BYTES", "104857600")
    monkeypatch.setenv("BADGE83_MAX_CSV_UPLOAD_BYTES", "20971520")
    monkeypatch.setenv("BADGE83_MAX_IMAGE_PIXELS", "100000000")

    assert config.get_max_png_upload_bytes() == 104857600
    assert config.get_max_csv_upload_bytes() == 20971520
    assert config.get_max_image_pixels() == 100000000


def test_upload_limits_fallback_to_large_defaults(monkeypatch):
    monkeypatch.delenv("BADGE83_MAX_PNG_UPLOAD_BYTES", raising=False)
    monkeypatch.delenv("BADGE83_MAX_CSV_UPLOAD_BYTES", raising=False)
    monkeypatch.delenv("BADGE83_MAX_IMAGE_PIXELS", raising=False)

    assert config.get_max_png_upload_bytes() == config.DEFAULT_MAX_PNG_UPLOAD_BYTES
    assert config.get_max_csv_upload_bytes() == config.DEFAULT_MAX_CSV_UPLOAD_BYTES
    assert config.get_max_image_pixels() == config.DEFAULT_MAX_IMAGE_PIXELS


def test_evm_config_defaults_keep_blockchain_optional(monkeypatch):
    monkeypatch.delenv("BADGE83_ANCHORING_PROVIDER", raising=False)
    monkeypatch.delenv("BADGE83_EVM_RPC_URL", raising=False)
    monkeypatch.delenv("BADGE83_EVM_CHAIN_ID", raising=False)
    monkeypatch.delenv("BADGE83_EVM_CONTRACT_ADDRESS", raising=False)
    monkeypatch.delenv("BADGE83_EVM_CONTRACT_VERSION", raising=False)
    monkeypatch.delenv("BADGE83_BLOCKCHAIN_VERIFY_BASE_URL", raising=False)
    monkeypatch.delenv("BADGE83_EVM_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("BADGE83_EVM_NETWORK_LABEL", raising=False)
    monkeypatch.delenv("BADGE83_EVM_EXPLORER_TX_URL_TEMPLATE", raising=False)
    monkeypatch.delenv("BADGE83_EVM_CONFIRMATION_TIMEOUT_SECONDS", raising=False)

    assert config.get_default_anchoring_provider() == "mock"
    assert config.get_evm_rpc_url() == ""
    assert config.get_evm_chain_id() is None
    assert config.get_evm_contract_address() == ""
    assert config.get_evm_contract_version() == "registry"
    assert config.get_blockchain_verify_base_url() == "https://mode83.ddns.net/blockchain/verify"
    assert config.get_evm_private_key() == ""
    assert config.get_evm_network_label() == "hardhat-local"
    assert config.get_evm_explorer_tx_url_template() == ""
    assert config.get_evm_confirmation_timeout_seconds() == 120


def test_evm_config_can_be_overridden(monkeypatch):
    monkeypatch.setenv("BADGE83_ANCHORING_PROVIDER", " evm ")
    monkeypatch.setenv("BADGE83_EVM_RPC_URL", " http://127.0.0.1:8545 ")
    monkeypatch.setenv("BADGE83_EVM_CHAIN_ID", "31337")
    monkeypatch.setenv("BADGE83_EVM_CONTRACT_ADDRESS", " 0x0000000000000000000000000000000000000001 ")
    monkeypatch.setenv("BADGE83_EVM_CONTRACT_VERSION", " v2 ")
    monkeypatch.setenv("BADGE83_BLOCKCHAIN_VERIFY_BASE_URL", " https://verify.example.test/ ")
    monkeypatch.setenv("BADGE83_EVM_PRIVATE_KEY", " 0xabc ")
    monkeypatch.setenv("BADGE83_EVM_NETWORK_LABEL", " hardhat-test ")
    monkeypatch.setenv("BADGE83_EVM_EXPLORER_TX_URL_TEMPLATE", " https://explorer.test/tx/{tx_hash} ")
    monkeypatch.setenv("BADGE83_EVM_CONFIRMATION_TIMEOUT_SECONDS", "30")

    assert config.get_default_anchoring_provider() == "evm"
    assert config.get_evm_rpc_url() == "http://127.0.0.1:8545"
    assert config.get_evm_chain_id() == 31337
    assert config.get_evm_contract_address() == "0x0000000000000000000000000000000000000001"
    assert config.get_evm_contract_version() == "v2"
    assert config.get_blockchain_verify_base_url() == "https://verify.example.test"
    assert config.get_evm_private_key() == "0xabc"
    assert config.get_evm_network_label() == "hardhat-test"
    assert config.get_evm_explorer_tx_url_template() == "https://explorer.test/tx/{tx_hash}"
    assert config.get_evm_confirmation_timeout_seconds() == 30


def test_evm_chain_id_invalid_returns_none(monkeypatch):
    monkeypatch.setenv("BADGE83_EVM_CHAIN_ID", "not-an-int")

    assert config.get_evm_chain_id() is None


def test_evm_contract_address_validation_is_format_only():
    assert config.is_valid_evm_address("0x0000000000000000000000000000000000000001") is True
    assert config.is_valid_evm_address("0xABCDEFabcdefABCDEFabcdefABCDEFabcdefABCD") is True
    assert config.is_valid_evm_address("") is False
    assert config.is_valid_evm_address("0x1234") is False
    assert config.is_valid_evm_address("not-an-address") is False
    assert config.is_valid_evm_address("javascript:alert(1)") is False


def test_evm_confirmation_timeout_invalid_or_non_positive_uses_default(monkeypatch):
    monkeypatch.setenv("BADGE83_EVM_CONFIRMATION_TIMEOUT_SECONDS", "0")
    assert config.get_evm_confirmation_timeout_seconds() == config.DEFAULT_EVM_CONFIRMATION_TIMEOUT_SECONDS

    monkeypatch.setenv("BADGE83_EVM_CONFIRMATION_TIMEOUT_SECONDS", "-10")
    assert config.get_evm_confirmation_timeout_seconds() == config.DEFAULT_EVM_CONFIRMATION_TIMEOUT_SECONDS

    monkeypatch.setenv("BADGE83_EVM_CONFIRMATION_TIMEOUT_SECONDS", "not-an-int")
    assert config.get_evm_confirmation_timeout_seconds() == config.DEFAULT_EVM_CONFIRMATION_TIMEOUT_SECONDS
