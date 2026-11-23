# eSusFarm – Acceptance test script

**Target:** `https://api-test.esusfarm.etherisc.com`  
**Status:** In progress – `api-test` on adapted Amoy product (`0x20b1…`, head `4888067` on Dokku).

## Preconditions

- [x] `API_JWT_SECRET` set on `esusfarm-api-test`
- [x] Bearer JWT issued to test team (secure channel)
- [x] Adapted contracts deployed on Amoy; `PRODUCT_CONTRACT_ADDRESS` / `TOKEN_CONTRACT_ADDRESS` set on Dokku (`0x20b1…` / `0x9467…`)
- [x] Test Mongo duplicate cleanup ran (2026-11-23; formal backup path: `mongo_backup_and_dedupe.py`)

## 1. Health (no auth)

```bash
curl -sS "https://api-test.esusfarm.etherisc.com/health/ping"
```

Expect: `{"response":"OK"}`.

## 2. Auth rejection

```bash
curl -sS -o /dev/null -w "%{http_code}" "https://api-test.esusfarm.etherisc.com/policy/all/json"
```

Expect: `401`.

## 3. Policy end-to-end (authenticated)

```bash
chmod +x scripts/acceptance_api_test.sh
./scripts/acceptance_api_test.sh
```

Or manual curl chain: `POST /location` → `/config` → `/risk` → `/person` → `/policy` with `Authorization: Bearer …` (issue via `scripts/issue_api_jwt.py` + Dokku `API_JWT_SECRET`).

- Create person / risk / policy with `Authorization: Bearer …`
- Response includes `id`, `nft`, `tx`
- Read-back `GET /policy/{id}` matches
- Tx visible on [Amoy Polygonscan](https://amoy.polygonscan.com/)

## 4. Idempotency

- Repeat same `externalId` and payload → `200`, same `id`
- Same `externalId`, different payload → `409`

## 5. Decimal amounts

- Policy with USD `2.01` premium → exact on-chain base units (`2010000` at 6 decimals for token accounting path)

## 6. Reconciliation 2026-09-23

| Record id | On-chain | Tx / reason |
|---|---|---|
| _TBD_ | | |

## Dry run sign-off

- [ ] Internal dry run completed
- [ ] Ready for eSusFarm access