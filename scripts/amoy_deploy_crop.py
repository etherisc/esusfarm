#!/usr/bin/env python3
"""Deploy adapted src/crop contracts on Polygon Amoy and wire to existing GIF instance."""

from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBS_JSON = ROOT / "lib/gif-next/deployments/polygonAmoy/libraries_80002.extracted.json"
OUT_DIR = ROOT / "deployments/polygonAmoy"

INSTANCE = os.getenv("INSTANCE_ADDRESS", "0x193491245A42d336ae5Fcb2d622d386041498a22")
REGISTRY = os.getenv("REGISTRY_ADDRESS", "0x7c19A25EF52c4E25Eb793d53B18F1811cE947455")
RPC = os.getenv("RPC_NODE_URL", "https://polygon-amoy-bor-rpc.publicnode.com")
BUNDLE_LIFETIME_DAYS = int(os.getenv("BUNDLE_LIFETIME_DAYS", "180"))
BUNDLE_STAKE = int(os.getenv("BUNDLE_STAKE_AMOUNT", str(1_000_000 * 10**6)))
GAS_PRICE = os.getenv("AMOY_GAS_PRICE", "30000000000")
ACCOUNT_INDEX = int(os.getenv("OPERATOR_ACCOUNT_INDEX", "2"))
TOKEN_REGISTRY_INDEX = int(os.getenv("TOKEN_REGISTRY_SIGNER_INDEX", "0"))
INSTANCE_OWNER_INDEX = int(os.getenv("INSTANCE_OWNER_SIGNER_INDEX", "10"))

# artifact path -> lib name in libraries JSON (BlocknumberLib key in json)
LIB_PATHS: dict[str, tuple[str, str]] = {
    "src/crop/Location.sol:LocationLib": ("LocationLib", "src/crop/Location.sol"),
    "src/crop/CropProductAuthorization.sol:CropProductAuthorization": (
        "CropProductAuthorization",
        "src/crop/CropProductAuthorization.sol",
    ),
    "src/crop/CropProduct.sol:CropProduct": ("CropProduct", "src/crop/CropProduct.sol"),
    "src/crop/CropPoolAuthorization.sol:CropPoolAuthorization": (
        "CropPoolAuthorization",
        "src/crop/CropPoolAuthorization.sol",
    ),
    "src/crop/CropPool.sol:CropPool": ("CropPool", "src/crop/CropPool.sol"),
}

AUTH_LIBS = [
    ("lib/gif-next/contracts/authorization/AccessAdminLib.sol", "AccessAdminLib"),
    ("lib/gif-next/contracts/type/Blocknumber.sol", "BlocknumberLib"),
    ("lib/gif-next/contracts/type/ObjectType.sol", "ObjectTypeLib"),
    ("lib/gif-next/contracts/type/RoleId.sol", "RoleIdLib"),
    ("lib/gif-next/contracts/type/Selector.sol", "SelectorLib"),
    ("lib/gif-next/contracts/type/String.sol", "StrLib"),
    ("lib/gif-next/contracts/type/Timestamp.sol", "TimestampLib"),
    ("lib/gif-next/contracts/type/Version.sol", "VersionPartLib"),
]

PRODUCT_LIBS = [
    ("lib/gif-next/contracts/type/Amount.sol", "AmountLib"),
    ("lib/gif-next/contracts/shared/ContractLib.sol", "ContractLib"),
    ("lib/gif-next/contracts/type/Fee.sol", "FeeLib"),
    ("lib/gif-next/contracts/type/NftId.sol", "NftIdLib"),
    ("lib/gif-next/contracts/type/ObjectType.sol", "ObjectTypeLib"),
    ("lib/gif-next/contracts/type/Referral.sol", "ReferralLib"),
    ("lib/gif-next/contracts/type/Seconds.sol", "SecondsLib"),
    ("lib/gif-next/contracts/type/String.sol", "StrLib"),
    ("lib/gif-next/contracts/type/Timestamp.sol", "TimestampLib"),
    ("lib/gif-next/contracts/type/UFixed.sol", "UFixedLib"),
    ("lib/gif-next/contracts/type/Version.sol", "VersionLib"),
    ("src/crop/Location.sol", "LocationLib"),
]

POOL_LIBS = [
    ("lib/gif-next/contracts/type/Amount.sol", "AmountLib"),
    ("lib/gif-next/contracts/shared/ContractLib.sol", "ContractLib"),
    ("lib/gif-next/contracts/type/Fee.sol", "FeeLib"),
    ("lib/gif-next/contracts/type/NftId.sol", "NftIdLib"),
    ("lib/gif-next/contracts/type/ObjectType.sol", "ObjectTypeLib"),
    ("lib/gif-next/contracts/type/Seconds.sol", "SecondsLib"),
    ("lib/gif-next/contracts/type/UFixed.sol", "UFixedLib"),
    ("lib/gif-next/contracts/type/Version.sol", "VersionLib"),
]


def run(cmd: list[str], *, env: dict | None = None) -> str:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        env=full_env,
        text=True,
        capture_output=True,
        check=False,
    )
    combined = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        sys.stderr.write(combined)
        redacted = [
            "(redacted)" if i > 0 and cmd[i - 1] in ("--mnemonic",) else a
            for i, a in enumerate(cmd)
        ]
        tail = combined[-2500:] if len(combined) > 2500 else combined
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(redacted)}\n{tail}"
        )
    return combined


def load_libs() -> dict[str, str]:
    data = json.loads(LIBS_JSON.read_text())
    return {k: v for k, v in data.items()}


def link_args(entries: list[tuple[str, str]], libs: dict[str, str]) -> list[str]:
    args: list[str] = []
    for path, name in entries:
        addr = libs.get(name)
        if not addr:
            raise KeyError(f"missing library address for {name}")
        args.append(f"{path}:{name}:{addr}")
    return args


def forge_create(
    mnemonic: str,
    contract: str,
    ctor: list[str],
    libs: list[tuple[str, str]],
    lib_addrs: dict[str, str],
) -> str:
    cmd = [
        "forge",
        "create",
        contract,
        "--rpc-url",
        RPC,
        "--legacy",
        "--gas-price",
        GAS_PRICE,
        "--broadcast",
        "--mnemonic",
        mnemonic,
        "--mnemonic-index",
        str(ACCOUNT_INDEX),
    ]
    for la in link_args(libs, lib_addrs):
        cmd.extend(["--libraries", la])
    if ctor:
        cmd.append("--constructor-args")
        cmd.extend(ctor)
    out = run(cmd, env={"FOUNDRY_PROFILE": os.getenv("FOUNDRY_PROFILE", "ci")})
    for pat in (
        r"Deployed to:\s+(0x[a-fA-F0-9]{40})",
        r'"contractAddress"\s*:\s*"(0x[a-fA-F0-9]{40})"',
        r'"deployedTo"\s*:\s*"(0x[a-fA-F0-9]{40})"',
    ):
        m = re.search(pat, out)
        if m:
            return m.group(1)
    tx_hash = re.search(r"Transaction hash:\s+(0x[a-fA-F0-9]{64})", out)
    if tx_hash:
        receipt = run(
            ["cast", "receipt", tx_hash.group(1), "--rpc-url", RPC, "--json"]
        )
        data = json.loads(receipt)
        addr = data.get("contractAddress")
        if addr and addr != "null":
            return str(addr)
    dbg = OUT_DIR / "last_forge_create.log"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dbg.write_text(out)
    raise RuntimeError(
        f"could not parse deploy address from forge output ({len(out)} bytes); see {dbg}"
    )


def cast_send(
    mnemonic: str,
    to: str,
    sig: str,
    *args: str,
    mnemonic_index: int | None = None,
) -> None:
    idx = ACCOUNT_INDEX if mnemonic_index is None else mnemonic_index
    cmd = [
        "cast",
        "send",
        to,
        sig,
        *args,
        "--rpc-url",
        RPC,
        "--legacy",
        "--gas-price",
        GAS_PRICE,
        "--mnemonic",
        mnemonic,
        "--mnemonic-index",
        str(idx),
    ]
    run(cmd)


def cast_call(to: str, sig: str, *args: str) -> str:
    cmd = ["cast", "call", to, sig, *args, "--rpc-url", RPC]
    return run(cmd)


def cast_call_uint(to: str, sig: str, *args: str) -> str:
    raw = cast_call(to, sig, *args).split()[0]
    return raw.split("[", 1)[0]


def load_local_env() -> None:
    path = ROOT / ".env.deploy.local"
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def ensure_mnemonic() -> str:
    m = os.getenv("OPERATOR_WALLET_MNEMONIC") or os.getenv("WALLET_MNEMONIC")
    if m:
        return m.strip()
    if os.getenv("FETCH_MNEMONIC_FROM_DOKKU") == "1":
        return subprocess.check_output(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "esusfarm-maint",
                "dokku config:get esusfarm-api-test OPERATOR_WALLET_MNEMONIC",
            ],
            text=True,
        ).strip()
    sys.exit(
        "Set OPERATOR_WALLET_MNEMONIC or WALLET_MNEMONIC, or FETCH_MNEMONIC_FROM_DOKKU=1"
    )


def main() -> None:
    load_local_env()
    if os.getenv("SKIP_FORGE_BUILD") != "1":
        subprocess.run(
            ["forge", "build"],
            cwd=ROOT,
            env={**os.environ, "FOUNDRY_PROFILE": os.getenv("FOUNDRY_PROFILE", "ci")},
            check=True,
        )
    mnemonic = ensure_mnemonic()
    lib_addrs = load_libs()
    deployer = run(
        [
            "cast",
            "wallet",
            "address",
            "--mnemonic",
            mnemonic,
            "--mnemonic-index",
            str(ACCOUNT_INDEX),
        ]
    )
    print("deployer", deployer)
    print("instance", INSTANCE, "registry", REGISTRY)

    instance_nft = cast_call_uint(INSTANCE, "getNftId()(uint256)")
    print("instance_nft", instance_nft)

    suffix = os.getenv("DEPLOY_SUFFIX") or secrets.token_hex(3)
    product_name = os.getenv("CROP_PRODUCT_NAME") or f"CropProduct_{suffix}"
    pool_name = os.getenv("CROP_POOL_NAME") or f"CropPool_{suffix}"

    accounting = os.getenv("ACCOUNTING_TOKEN_ADDRESS")
    if not accounting:
        accounting = forge_create(
            mnemonic,
            "src/crop/AccountingToken.sol:AccountingToken",
            [],
            [],
            lib_addrs,
        )
    print("AccountingToken", accounting)

    location_lib = os.getenv("LOCATION_LIB_ADDRESS")
    if not location_lib:
        location_lib = forge_create(
            mnemonic,
            "src/crop/Location.sol:LocationLib",
            [],
            [],
            lib_addrs,
        )
    lib_addrs = {**lib_addrs, "LocationLib": location_lib}
    print("LocationLib", location_lib)

    product_auth = os.getenv("CROP_PRODUCT_AUTH_ADDRESS")
    if not product_auth:
        product_auth = forge_create(
            mnemonic,
            "src/crop/CropProductAuthorization.sol:CropProductAuthorization",
            [product_name],
            AUTH_LIBS,
            lib_addrs,
        )
    print("CropProductAuthorization", product_auth)

    crop_product = os.getenv("CROP_PRODUCT_ADDRESS")
    if not crop_product:
        crop_product = forge_create(
            mnemonic,
            "src/crop/CropProduct.sol:CropProduct",
            [REGISTRY, instance_nft, product_name, product_auth],
            PRODUCT_LIBS,
            lib_addrs,
        )
    print("CropProduct", crop_product)

    token_registry = cast_call(
        REGISTRY,
        "getTokenRegistryAddress()(address)",
    )
    for label, fn, fn_args in (
        (
            "registerToken",
            "registerToken(address)",
            (accounting,),
        ),
        (
            "setActiveForVersion",
            "setActiveForVersion(uint96,address,uint8,bool)",
            ("80002", accounting, "3", "true"),
        ),
    ):
        try:
            cast_send(
                mnemonic,
                token_registry,
                fn,
                *fn_args,
                mnemonic_index=TOKEN_REGISTRY_INDEX,
            )
        except RuntimeError as exc:
            msg = str(exc)
            if label == "registerToken" and "AlreadyRegistered" in msg:
                print("token already registered; continuing")
            elif label == "setActiveForVersion":
                print("WARN: setActiveForVersion failed; continuing:", msg[-300:])
            else:
                raise

    product_nft = cast_call_uint(crop_product, "getNftId()(uint256)")
    if product_nft == "0":
        cast_send(
            mnemonic,
            INSTANCE,
            "registerProduct(address,address)",
            crop_product,
            accounting,
        )
        product_nft = cast_call_uint(crop_product, "getNftId()(uint256)")
    print("product_nft", product_nft)

    reader = cast_call(INSTANCE, "getInstanceReader()(address)")
    role_out = cast_call_uint(
        reader, "getRoleForName(string)(uint64,bool)", "ProductOperatorRole"
    )
    try:
        cast_send(
            mnemonic,
            INSTANCE,
            "grantRole(uint64,address)",
            role_out,
            deployer,
            mnemonic_index=INSTANCE_OWNER_INDEX,
        )
    except RuntimeError as exc:
        print("WARN: grantRole skipped:", str(exc)[-200:])

    dec = 6
    min_p = str(10 * 10**dec)
    max_p = str(99 * 10**dec)
    min_si = str(200 * 10**dec)
    max_si = str(1000 * 10**dec)
    try:
        cast_send(
            mnemonic,
            crop_product,
            "setConstants(uint96,uint96,uint96,uint96,uint8)",
            min_p,
            max_p,
            min_si,
            max_si,
            "5",
        )
    except RuntimeError as exc:
        print("WARN: setConstants skipped:", str(exc)[-200:])

    pool_auth = os.getenv("CROP_POOL_AUTH_ADDRESS")
    if not pool_auth:
        pool_auth = forge_create(
            mnemonic,
            "src/crop/CropPoolAuthorization.sol:CropPoolAuthorization",
            [pool_name],
            AUTH_LIBS,
            lib_addrs,
        )
    print("CropPoolAuthorization", pool_auth)

    crop_pool = os.getenv("CROP_POOL_ADDRESS")
    if not crop_pool:
        crop_pool = forge_create(
            mnemonic,
            "src/crop/CropPool.sol:CropPool",
            [REGISTRY, product_nft, pool_name, pool_auth, str(BUNDLE_LIFETIME_DAYS)],
            POOL_LIBS,
            lib_addrs,
        )
    print("CropPool", crop_pool)

    pool_nft = cast_call_uint(crop_pool, "getNftId()(uint256)")
    if pool_nft == "0":
        cast_send(mnemonic, crop_product, "registerComponent(address)", crop_pool)
        pool_nft = cast_call_uint(crop_pool, "getNftId()(uint256)")
    print("pool_nft", pool_nft)

    pool_handler = cast_call(crop_pool, "getTokenHandler()(address)")
    cast_send(
        mnemonic,
        accounting,
        "approve(address,uint256)",
        pool_handler,
        str(BUNDLE_STAKE),
    )
    cast_send(mnemonic, crop_pool, "createBundle(uint96)", str(BUNDLE_STAKE))
    bundle_nft = ""
    print("bundle created (stake)", BUNDLE_STAKE)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "chainId": 80002,
        "instance": INSTANCE,
        "registry": REGISTRY,
        "instanceNftId": instance_nft,
        "accountingToken": accounting,
        "locationLib": location_lib,
        "cropProductAuthorization": product_auth,
        "cropProduct": crop_product,
        "productNftId": product_nft,
        "cropPoolAuthorization": pool_auth,
        "cropPool": crop_pool,
        "poolNftId": pool_nft,
        "bundleNftId": bundle_nft or None,
        "bundleLifetimeDays": BUNDLE_LIFETIME_DAYS,
        "bundleStake": BUNDLE_STAKE,
        "deployer": deployer,
    }
    out_path = OUT_DIR / f"crop_deploy_{suffix}.json"
    out_path.write_text(json.dumps(record, indent=2) + "\n")
    print("wrote", out_path)


if __name__ == "__main__":
    main()