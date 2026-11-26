# 23 September 2026 session — policy ids (eSusFarm)

| API `_id` / `id` | `externalId` | In test Mongo (2026-11-26) | Notes |
|------------------|--------------|----------------------------|--------|
| `-ZjMGbeFkx1E` | `CANARY-20260923-1` | **Yes** | Mongo only; no `tx` / `nft` |
| `kGUm_i5vr7F_` | `CANARY-20260923-DECIMAL` | **Yes** | Mongo only; fractional amounts in DB (legacy API) |
| `vygyWfvfflAK` | _(unknown)_ | **No** | Not present in any collection; not in ESF-1.09 dedupe export. Likely never persisted, or removed before 2026-11-23 backup. |

Re-run export: `scripts/mongo_policy_reconciliation_export.py` on `esusfarm-api-test`.