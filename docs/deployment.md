# eSusFarm – Deployment runbook

Mechanical steps for on-chain setup and API configuration. **Production steps are placeholder until test dry run passes.**

## Environments

| Env | API | Dokku app | Chain |
|---|---|---|---|
| Test | `https://api-test.esusfarm.etherisc.com` | `esusfarm-api-test` | Polygon Amoy (80002) |
| Prod | `https://api.esusfarm.etherisc.com` | `esusfarm-api` | Polygon mainnet — **not in phase 1** |

Host: `162.55.209.69` (same for both apps).

## Prerequisites

- Operator wallet mnemonic in Dokku config (`OPERATOR_WALLET_MNEMONIC`, `OPERATOR_ACCOUNT_INDEX`).
- RPC URL in Dokku (`RPC_NODE_URL`).
- Adapted contracts built from this repo (`src/crop/`, `lib/gif-next` at `v3.0.0-beta.3`).
- Explore Amoy from operator `0xad8308964bcB8BfaCa77A625478D4D4E683CD433` to locate existing GIF v3 instance/registry.

## ESF-1.03 – Amoy (test) – checklist

_To be filled as deploy is executed._

1. [ ] Record GIF instance and registry addresses (reuse existing Amoy GIF v3).
2. [ ] Deploy `AccountingToken` (“eSusFarm UGX”, 6 decimals).
3. [ ] Deploy `CropProduct` + `CropPool` (+ authorization contracts) from this repo; link to instance.
4. [ ] Create bundle with configured `bundleLifetimeDays` and capacity; fund with Accounting Tokens only.
5. [ ] Verify source on Amoy Polygonscan.
6. [ ] Set Dokku **test** only: `PRODUCT_CONTRACT_ADDRESS`, `TOKEN_CONTRACT_ADDRESS`, `API_JWT_SECRET` (see below).
7. [ ] Record in table:

| Item | Value |
|---|---|
| GIF instance | |
| Registry | |
| Accounting token | |
| Crop product | |
| Crop pool | |
| Bundle NFT id | |
| Bundle lifetime (days) | |
| Bundle capacity | |

## API secrets (test)

| Variable | Purpose |
|---|---|
| `API_JWT_SECRET` | HS256 secret for fixed Bearer JWT (issue new value per env). |
| `API_JWT_ALGORITHM` | `HS256` (default). |

JWT is delivered to eSusFarm through a secure channel (not plain email).

## Local mock deploy (Anvil only)

Unchanged: `forge script script/MockSetup.s.sol` deploys **mocks** under `src/mock/` for offline API dev without a full GIF instance.

## Prod (deferred)

See Implementation Plan ESF-1.11 after acceptance dry run and decisions D1–D3.