from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from pathlib import Path
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import (
    get_evm_chain_id,
    get_evm_contract_address,
    get_evm_network_label,
    get_evm_private_key,
    get_evm_rpc_url,
    is_valid_evm_address,
)
from app.proofs.anchoring_providers import EvmAnchoringProvider, SHA256_CREDENTIAL_HASH_RE


def _load_env_file(path: Path) -> None:
    """Charge un fichier env local simple sans afficher les secrets."""

    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _rpc_call(rpc_url: str, method: str, params: list[object]) -> dict[str, object]:
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = Request(rpc_url, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _print_config_summary() -> bool:
    rpc_url = get_evm_rpc_url()
    contract = get_evm_contract_address()
    private_key = get_evm_private_key()
    chain_id = get_evm_chain_id()

    contract_valid = is_valid_evm_address(contract)
    config_ok = bool(rpc_url and contract and private_key and contract_valid)

    print("config.rpc_set=", bool(rpc_url))
    print("config.chain_id=", chain_id)
    print("config.contract_set=", bool(contract))
    print("config.contract_valid=", contract_valid)
    print("config.private_key_set=", bool(private_key))
    print("config.network=", get_evm_network_label())
    print("config.ready_for_anchor=", config_ok)
    return config_ok


def _check_rpc_and_contract() -> bool:
    rpc_url = get_evm_rpc_url()
    contract = get_evm_contract_address()
    if not rpc_url or not contract or not is_valid_evm_address(contract):
        print("rpc_check.skipped= True")
        return False

    chain = _rpc_call(rpc_url, "eth_chainId", [])
    code = _rpc_call(rpc_url, "eth_getCode", [contract, "latest"])
    chain_id_hex = chain.get("result")
    code_value = str(code.get("result") or "")
    has_code = bool(code_value and code_value != "0x")

    print("rpc.chain_id_hex=", chain_id_hex)
    print("rpc.chain_id_decimal=", int(str(chain_id_hex), 16) if chain_id_hex else None)
    print("rpc.contract_has_code=", has_code)
    print("rpc.contract_code_prefix=", code_value[:10] if code_value else None)
    return has_code


def _short_hash(credential_hash: str) -> str:
    return credential_hash[:18] + "..." if len(credential_hash) > 18 else credential_hash


def _anchor_and_verify(credential_hash: str) -> int:
    provider = EvmAnchoringProvider()
    result = provider.anchor({"credential_hash": credential_hash})
    print("anchor.credential_hash_prefix=", _short_hash(credential_hash))
    print("anchor.status=", result.status)
    print("anchor.network=", result.network)
    print("anchor.tx_hash=", result.tx_hash)
    print("anchor.block_number=", result.block_number)
    print("anchor.error_message=", result.error_message)

    if result.status != "anchored":
        return 1

    verification = provider.verifier_hash_ancre(credential_hash)
    print("verification.status=", verification.get("status"))
    print("verification.verified=", verification.get("verified"))
    print("verification.network=", verification.get("network"))
    print("verification.error_message=", verification.get("error_message"))
    return 0 if verification.get("verified") is True else 1


def _revoke_and_status(credential_hash: str) -> int:
    provider = EvmAnchoringProvider()
    result = provider.revoke({"credential_hash": credential_hash})
    print("revoke.credential_hash_prefix=", _short_hash(credential_hash))
    print("revoke.status=", result.status)
    print("revoke.network=", result.network)
    print("revoke.tx_hash=", result.tx_hash)
    print("revoke.block_number=", result.block_number)
    print("revoke.error_message=", result.error_message)

    if result.status != "revoked":
        return 1

    return _status_only(credential_hash, require_available=True, require_revoked=True)


def _anchor_revoke_and_status(credential_hash: str) -> int:
    anchor_exit = _anchor_and_verify(credential_hash)
    if anchor_exit != 0:
        return anchor_exit
    return _revoke_and_status(credential_hash)


def _verify_only(credential_hash: str) -> int:
    provider = EvmAnchoringProvider()
    verification = provider.verifier_hash_ancre(credential_hash)
    print("verify.credential_hash_prefix=", _short_hash(credential_hash))
    print("verification.status=", verification.get("status"))
    print("verification.verified=", verification.get("verified"))
    print("verification.network=", verification.get("network"))
    print("verification.error_message=", verification.get("error_message"))
    return 0 if verification.get("available") is True else 1


def _status_only(credential_hash: str, *, require_available: bool = True, require_revoked: bool = False) -> int:
    provider = EvmAnchoringProvider()
    status = provider.get_hash_status(credential_hash)
    print("status.credential_hash_prefix=", _short_hash(credential_hash))
    print("status.status=", status.get("status"))
    print("status.anchored=", status.get("anchored"))
    print("status.revoked=", status.get("revoked"))
    print("status.network=", status.get("network"))
    print("status.error_message=", status.get("error_message"))
    if require_revoked:
        return 0 if status.get("anchored") is True and status.get("revoked") is True else 1
    if require_available:
        return 0 if status.get("available") is True else 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test EVM Badge83 sans afficher RPC complet ni clé privée.",
    )
    parser.add_argument("--env-file", default="badge83.env", help="Fichier env local à charger si présent.")
    parser.add_argument(
        "--anchor-random-hash",
        action="store_true",
        help="Envoie une transaction EVM avec un hash aléatoire sha256:<64 hex>.",
    )
    parser.add_argument(
        "--credential-hash",
        help="Hash sha256:<64 hex> à ancrer. Envoie une transaction EVM.",
    )
    parser.add_argument(
        "--verify-hash",
        help="Hash sha256:<64 hex> à vérifier en lecture seule, sans transaction.",
    )
    parser.add_argument(
        "--revoke-hash",
        help="Hash sha256:<64 hex> à révoquer. Envoie une transaction EVM revoke(bytes32).",
    )
    parser.add_argument(
        "--status-hash",
        help="Hash sha256:<64 hex> à lire via getStatus(bytes32), sans transaction.",
    )
    parser.add_argument(
        "--anchor-and-revoke-random-hash",
        action="store_true",
        help="Ancre puis révoque un hash aléatoire sha256:<64 hex>.",
    )
    args = parser.parse_args()

    _load_env_file(Path(args.env_file))
    config_ok = _print_config_summary()
    rpc_ok = _check_rpc_and_contract()

    if args.verify_hash:
        if not SHA256_CREDENTIAL_HASH_RE.match(args.verify_hash):
            print("error= invalid --verify-hash, expected sha256:<64 hex>")
            return 2
        return _verify_only(args.verify_hash)

    if args.status_hash:
        if not SHA256_CREDENTIAL_HASH_RE.match(args.status_hash):
            print("error= invalid --status-hash, expected sha256:<64 hex>")
            return 2
        return _status_only(args.status_hash)

    if args.revoke_hash:
        if not SHA256_CREDENTIAL_HASH_RE.match(args.revoke_hash):
            print("error= invalid --revoke-hash, expected sha256:<64 hex>")
            return 2
        if not config_ok or not rpc_ok:
            print("error= EVM configuration or contract RPC check is not ready for revocation")
            return 1
        return _revoke_and_status(args.revoke_hash)

    credential_hash = args.credential_hash
    if args.anchor_random_hash:
        credential_hash = "sha256:" + secrets.token_hex(32)
    if args.anchor_and_revoke_random_hash:
        credential_hash = "sha256:" + secrets.token_hex(32)

    if credential_hash:
        if not SHA256_CREDENTIAL_HASH_RE.match(credential_hash):
            print("error= invalid credential hash, expected sha256:<64 hex>")
            return 2
        if not config_ok or not rpc_ok:
            print("error= EVM configuration or contract RPC check is not ready for anchoring")
            return 1
        if args.anchor_and_revoke_random_hash:
            return _anchor_revoke_and_status(credential_hash)
        return _anchor_and_verify(credential_hash)

    print("action= no transaction sent; use --anchor-random-hash or --anchor-and-revoke-random-hash")
    return 0 if config_ok and rpc_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())