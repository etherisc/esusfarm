#!/usr/bin/env python3
"""Backup and dedupe Person/Policy by externalId on test MongoDB."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient


def get_db(uri: str):
    client = MongoClient(uri)
    return client, client.get_default_database()


def backup_collection(db, name: str, out_dir: Path) -> None:
    docs = list(db[name].find({}))
    path = out_dir / f"{name}.json"
    path.write_text(json.dumps(docs, default=str, indent=2))
    print(f"backup {name}: {len(docs)} docs -> {path}")


def unset_blank_external_ids(db, name: str, dry_run: bool) -> int:
    n = db[name].count_documents({"externalId": ""})
    if dry_run or n == 0:
        return n
    return db[name].update_many({"externalId": ""}, {"$unset": {"externalId": ""}}).modified_count


def dedupe(db, name: str, dry_run: bool) -> list[dict]:
    removed: list[dict] = []
    groups: dict[str, list] = defaultdict(list)
    for doc in db[name].find({"externalId": {"$exists": True, "$type": "string", "$gt": ""}}):
        groups[str(doc["externalId"])].append(doc)

    for eid, docs in groups.items():
        if len(docs) < 2:
            continue
        docs.sort(key=lambda d: d.get("id") or str(d.get("_id", "")))
        keep, drop = docs[0], docs[1:]
        for doc in drop:
            removed.append(
                {
                    "collection": name,
                    "externalId": eid,
                    "removedId": doc.get("id"),
                    "keptId": keep.get("id"),
                }
            )
            if not dry_run:
                key = {"id": doc["id"]} if doc.get("id") else {"_id": doc["_id"]}
                db[name].delete_one(key)

    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-uri", default=None, help="Defaults to MONGO_URL env")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup-dir", default=None)
    args = parser.parse_args()

    import os

    uri = args.mongo_uri or os.environ.get("MONGO_URL")
    if not uri:
        raise SystemExit("Set MONGO_URL or --mongo-uri")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = Path(args.backup_dir or f"./mongo-backup-{stamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)

    client, db = get_db(uri)
    for coll in ("Person", "Policy"):
        if coll in db.list_collection_names():
            backup_collection(db, coll, backup_dir)

    report: list[dict] = []
    for coll in ("Person", "Policy"):
        if coll in db.list_collection_names():
            blank = unset_blank_external_ids(db, coll, args.dry_run)
            if blank:
                print(f"{coll}: unset blank externalId on {blank} docs" + (" (dry-run count)" if args.dry_run else ""))
            report.extend(dedupe(db, coll, args.dry_run))

    report_path = backup_dir / "dedupe_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"dedupe report: {len(report)} removals -> {report_path}")
    if args.dry_run:
        print("(dry-run; no documents deleted)")


if __name__ == "__main__":
    main()