#!/usr/bin/env python3
"""Export Policy collection for acceptance reconciliation (read-only)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

from pymongo import MongoClient

# Legacy vs adapted CropProduct (Amoy)
LEGACY_PRODUCT = "0x6d39a6458aba448d3c5cbC00f2135352197e6091".lower()
ADAPTED_PRODUCT = "0x20b1c9f88a7aaa4f7457e6f5aCAF05033e13229C".lower()


def classify(doc: dict) -> tuple[str, str]:
    tx = doc.get("tx")
    nft = doc.get("nft")
    if tx and nft is not None:
        return "on-chain complete", "tx and nft present"
    if tx:
        return "on-chain partial", "tx present; nft missing (legacy API path)"
    return "mongo only", "no tx — never synced or sync failed"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-url", default=os.environ.get("MONGO_URL"))
    parser.add_argument("--out-dir", type=Path, default=Path("docs/reconciliation"))
    parser.add_argument(
        "--session-date",
        default="2026-09-23",
        help="Scope reference date (subscriptionDate filter; see README in out dir)",
    )
    args = parser.parse_args()
    if not args.mongo_url:
        print("Set MONGO_URL or pass --mongo-url", file=sys.stderr)
        sys.exit(1)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    coll = MongoClient(args.mongo_url).get_default_database()["Policy"]
    docs = list(coll.find({}))
    docs.sort(key=lambda d: (d.get("subscriptionDate") or "", d.get("externalId") or "", d.get("_id") or ""))

    session = [d for d in docs if str(d.get("subscriptionDate", "")).startswith(args.session_date)]

    rows = []
    for doc in docs:
        status, note = classify(doc)
        rows.append(
            {
                "api_id": doc.get("id") or doc.get("_id"),
                "_id": doc.get("_id"),
                "externalId": doc.get("externalId"),
                "subscriptionDate": doc.get("subscriptionDate"),
                "currency": doc.get("currency"),
                "sumInsuredAmount": doc.get("sumInsuredAmount"),
                "premiumAmount": doc.get("premiumAmount"),
                "tx": doc.get("tx"),
                "nft": doc.get("nft"),
                "on_chain_status": status,
                "notes": note,
            }
        )

    csv_path = args.out_dir / "api-test-policies-all.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        w.writeheader()
        w.writerows(rows)

    summary = {
        "exported_at_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "total_policies": len(docs),
        "with_tx": sum(1 for r in rows if r["tx"]),
        "with_nft": sum(1 for r in rows if r["nft"] is not None),
        "session_date_filter": args.session_date,
        "policies_matching_subscription_date": len(session),
        "note": (
            "Mongo Policy documents have no createdAt field. "
            "Scope '23 September 2026' cannot be filtered by insert date without a backup or eSusFarm externalId list."
        ),
    }
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (args.out_dir / "session-date-policies.json").write_text(
        json.dumps([{k: d.get(k) for k in ("id", "_id", "externalId", "subscriptionDate", "tx", "nft")} for d in session], indent=2)
    )
    print(json.dumps(summary, indent=2))
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()