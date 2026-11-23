#!/usr/bin/env python3
"""Fix externalId duplicates blocking unique index on test Mongo (run inside Dokku)."""

from __future__ import annotations

import os
from collections import defaultdict

from pymongo import MongoClient

uri = os.environ.get("MONGO_URL")
if not uri:
    raise SystemExit("MONGO_URL not set")

client = MongoClient(uri)
db = client.get_default_database()

for coll in ("Person", "Policy"):
    if coll not in db.list_collection_names():
        print(coll, "missing")
        continue

    r0 = db[coll].update_many({"externalId": ""}, {"$unset": {"externalId": ""}})
    print(coll, "unset_blank", r0.modified_count)

    for idx in list(db[coll].list_indexes()):
        if idx["name"].startswith("externalId"):
            db[coll].drop_index(idx["name"])
            print(coll, "dropped_index", idx["name"])

    groups: dict[str, list] = defaultdict(list)
    for doc in db[coll].find({"externalId": {"$exists": True, "$type": "string", "$gt": ""}}):
        groups[str(doc["externalId"])].append(doc)

    removed = 0
    for eid, docs in groups.items():
        if len(docs) < 2:
            continue
        docs.sort(key=lambda d: d.get("id") or str(d.get("_id", "")))
        for doc in docs[1:]:
            key = {"id": doc["id"]} if doc.get("id") else {"_id": doc["_id"]}
            db[coll].delete_one(key)
            removed += 1
    print(coll, "dedupe_removed", removed)

print("done")