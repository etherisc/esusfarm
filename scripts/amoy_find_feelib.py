#!/usr/bin/env python3
"""Find FeeLib on Polygon Amoy by deploy order + bytecode match."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

RPC = "https://polygon-amoy-bor-rpc.publicnode.com"
GIF_NEXT = Path(__file__).resolve().parents[1] / "lib" / "gif-next"
AMT = "0xf092905d3bb8a2b957422d89dcbb6ea7d4462b59"
UFIX = "0x64e533ae3af71b091bdb0d53e6dad95ee4a99efe"

# libraries_80002.extracted.json + manual merges (same GIF generation)
# Verified via legacy CropPool 0x58123… push20 + bytecode match (Nov 2026).
FEELIB_AMOY = "0x2f58f86f3cfea7ad6010d0f136a594cf61d23876"
LEGACY_CROP_POOL = "0x58123e8d38df7442ce6c7bbcc58f6adf7e87347a"

KNOWN_LIBS = {
    "AccessAdminLib": "0xd94b55c9cf7fe87fb3fac820e36ed14d9f3c4305",
    "AmountLib": "0xf092905d3bb8a2b957422d89dcbb6ea7d4462b59",
    "BlocknumberLib": "0xdcaa78081570581262dd1a1dfa6cad1ec642b410",
    "ChainIdLib": "0x6a5e82ed51101ddd6ed7afd3a9d9856dabd91ac6",
    "ClaimIdLib": "0x4ac8a7a2e4aa5a64eb8d010033173631c2d4fb90",
    "ContractLib": "0x0dabdecb81efe5a6b9993a5384542babf95f959e",
    "Key32Lib": "0xd8ee94a7c26a42148f498655c33b914eca4e8749",
    "LocationLib": "0xda59705c38a8402e1b63e01675731dbc13beaefe",
    "NftIdLib": "0xf32c2604bd858c6d254066b425afe316b89e2478",
    "ObjectTypeLib": "0xa5c47093879cc30665d4bae31f01820281909d73",
    "PayoutIdLib": "0xe612715d54374daea71f1c421c2010407392651a",
    "PolicyServiceLib": "0xfb514a773770b965c79e1554836411ecf537cbe8",
    "ReferralLib": "0x2707ce4af06fb46588fd134d2e23c925a6f67a52",
    "RequestIdLib": "0x47f9a1f04cdc94cb0e6ca714390dbfc9616cede8",
    "RiskIdLib": "0xe7604ddb05c5cf0c2d5704b0fb495e6c7a471344",
    "RoleIdLib": "0xb167a26dcf010b4a0e81aae934610c3fb5a5abd7",
    "SecondsLib": "0x96f1449587d4086fd507cbee0056ac6122dbdd6f",
    "SelectorLib": "0x95ac6dfcf65cf7edf13241c18d7bc269a784b16f",
    "StrLib": "0x930a9318748f297d337ab2faf88a282d03ec4ad3",
    "TimestampLib": "0xe6d41948ebfc8eb77090e7aa33ad9f429880f828",
    "UFixedLib": "0x64e533ae3af71b091bdb0d53e6dad95ee4a99efe",
    "VersionLib": "0x5dea4f887be469b80dd3825140858ac16b3175bd",
    "VersionPartLib": "0xf8036fce716f05df011af3291a31aa5a363cef57",
}

# deployLibraries() order from lib/gif-next/scripts/libs/libraries.ts (subset for FeeLib position)
DEPLOY_ORDER = [
    "VersionLib",
    "VersionPartLib",
    "Key32Lib",
    "NftIdLib",
    "ChainIdLib",
    "ObjectTypeLib",
    "BlocknumberLib",
    "ContractLib",
    "SecondsLib",
    "TimestampLib",
    "AmountLib",
    "UFixedLib",
    "FeeLib",
    "PoolLib",
]


def cast(args: list[str]) -> str:
    return subprocess.check_output(["cast", *args, "--rpc-url", RPC], text=True).strip()


def code_len_at_block(addr: str, block: int) -> int:
    out = subprocess.check_output(
        ["cast", "code", addr, "--block", str(block), "--rpc-url", RPC],
        text=True,
    ).strip()
    if out in ("0x", "0x0", ""):
        return 0
    return (len(out) - 2) // 2


def first_deployment_block(addr: str, latest: int) -> int:
    if code_len_at_block(addr, latest) == 0:
        return -1
    lo, hi = 0, latest
    while lo < hi:
        mid = (lo + hi) // 2
        if code_len_at_block(addr, mid) > 0:
            hi = mid
        else:
            lo = mid + 1
    return lo


def strip_library_prologue(code: bytes) -> bytes:
    if len(code) > 22 and code[0] == 0x73:
        return code[22:]
    return code


def build_linked_feelib() -> bytes:
    art_path = next((GIF_NEXT / "artifacts_forge").rglob("FeeLib.json"))
    art = json.loads(art_path.read_text())
    obj = bytearray.fromhex(
        re.sub(r"__\$[a-fA-F0-9]+\$__", "00" * 20, art["deployedBytecode"]["object"].replace("0x", ""))
    )
    refs = art["deployedBytecode"]["linkReferences"]
    known = {"AmountLib": bytes.fromhex(AMT[2:]), "UFixedLib": bytes.fromhex(UFIX[2:])}
    for _fp, contracts in refs.items():
        for lib_name, slots in contracts.items():
            if lib_name not in known:
                continue
            addr_bytes = known[lib_name]
            for slot in slots:
                start, length = slot["start"], slot["length"]
                obj[start : start + length] = addr_bytes
    return bytes(obj)


def code_match_feelib(addr: str, template: bytes) -> int:
    on = bytes.fromhex(cast(["code", addr])[2:])
    return sum(1 for a, b in zip(strip_library_prologue(on), strip_library_prologue(template)) if a == b)


def main() -> None:
    score = code_match_feelib(FEELIB_AMOY, build_linked_feelib())
    if score > 2000:
        print(json.dumps({"FeeLib": FEELIB_AMOY, "match_bytes": score, "source": "legacy CropPool"}))
        return

    template = build_linked_feelib()
    print(f"FeeLib template len {len(template)}", file=sys.stderr)

    # GIF v3 + crop deploy window on Amoy (from Polygonscan deployer 0x481f…)
    window_lo, window_hi = 15_951_000, 15_952_200
    creator = "0x481f666C700D235B8B5e1371b8c036Cc1A877405"
    known_addrs = {v.lower() for v in KNOWN_LIBS.values()}

    best = ("", 0)
    for block in range(window_lo, window_hi + 1):
        try:
            blk = json.loads(
                subprocess.check_output(["cast", "block", str(block), "--json", "--rpc-url", RPC], text=True)
            )
        except subprocess.CalledProcessError:
            continue
        for tx in blk.get("transactions", []):
            if not isinstance(tx, dict):
                continue
            if tx.get("from", "").lower() != creator.lower() or tx.get("to") not in (None, "0x", "0x0000000000000000000000000000000000000000"):
                continue
            # contract creation
            try:
                receipt = json.loads(
                    subprocess.check_output(
                        ["cast", "receipt", tx["hash"], "--json", "--rpc-url", RPC], text=True
                    )
                )
            except subprocess.CalledProcessError:
                continue
            addr = receipt.get("contractAddress")
            if not addr:
                continue
            if addr.lower() in known_addrs:
                continue
            score = code_match_feelib(addr, template)
            print(f"  block {block} new {addr} score {score}", file=sys.stderr)
            if score > best[1]:
                best = (addr, score)
            if score > 200:
                print(
                    json.dumps(
                        {
                            "FeeLib": addr,
                            "match_bytes": score,
                            "deploy_block": block,
                            "tx": tx["hash"],
                        }
                    )
                )
                return

    print(json.dumps({"FeeLib": None, "best_score": best[1], "best_addr": best[0] or None}))
    sys.exit(1)


if __name__ == "__main__":
    main()