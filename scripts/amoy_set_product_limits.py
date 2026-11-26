#!/usr/bin/env python3
"""Raise CropProduct min/max amounts on Amoy for api-test (1–5M UGX major units, 6 decimals)."""

from __future__ import annotations

import os
import subprocess
import sys

DEC = 6
MIN_MAJOR = int(os.environ.get("POLICY_MIN_MAJOR", "1"))
MAX_MAJOR = int(os.environ.get("POLICY_MAX_MAJOR", "5000000"))
PRODUCT = os.environ.get(
    "CROP_PRODUCT_ADDRESS", "0x20b1c9F88a7AaA4f7457e6f5aCAF05033e13229C"
)
RPC = os.environ.get("RPC_NODE_URL", "https://polygon-amoy-bor-rpc.publicnode.com")


def main() -> None:
    mnemonic = os.environ.get("OPERATOR_WALLET_MNEMONIC")
    if not mnemonic and os.environ.get("FETCH_MNEMONIC_FROM_DOKKU") == "1":
        mnemonic = subprocess.check_output(
            ["ssh", "-o", "BatchMode=yes", "esusfarm-maint", "dokku", "config:get", "esusfarm-api-test", "OPERATOR_WALLET_MNEMONIC"],
            text=True,
        ).strip()
    if not mnemonic:
        print("Set OPERATOR_WALLET_MNEMONIC or FETCH_MNEMONIC_FROM_DOKKU=1", file=sys.stderr)
        sys.exit(1)

    idx = os.environ.get("OPERATOR_ACCOUNT_INDEX", "2")
    scale = 10**DEC
    args = [
        str(MIN_MAJOR * scale),
        str(MAX_MAJOR * scale),
        str(MIN_MAJOR * scale),
        str(MAX_MAJOR * scale),
        "5",
    ]
    cmd = [
        "cast",
        "send",
        PRODUCT,
        "setConstants(uint96,uint96,uint96,uint96,uint8)",
        *args,
        "--rpc-url",
        RPC,
        "--mnemonic",
        mnemonic,
        "--mnemonic-index",
        idx,
    ]
    print("setConstants", args, "on", PRODUCT)
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()