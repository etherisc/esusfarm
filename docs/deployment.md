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

## Legacy Amoy references (2024-12-23 deploy)

| Item | Value |
|---|---|
| Chain | Polygon Amoy (80002) |
| Operator | `0xad8308964bcB8BfaCa77A625478D4D4E683CD433` |
| CropProduct (legacy) | `0x6d39A6458ABa448d3C5cbC00f2135352197e6091` |
| GIF Instance | `0x193491245A42d336ae5Fcb2d622d386041498a22` |
| Registry | `0x7c19A25EF52c4E25Eb793d53B18F1811cE947455` |
| Accounting token (legacy) | `0x612ef62560Ceb3b114fC302f7F54F4D493371D6B` |
| Product NFT id | `208000205` |
| Bundle id (expired) | `228000205` (90-day bundle; do not reuse) |
| Amoy RPC (public) | `https://polygon-amoy-bor-rpc.publicnode.com` |

Discover current instance/registry:

```bash
RPC_NODE_URL=<amoy-rpc> uv run python scripts/amoy_discover.py
```

### Reuse existing GIF instance

Set when deploying **new** adapted CropProduct/CropPool (Hardhat script in `lib/gif-next/scripts/deploy_crop_components.ts` or future Forge script):

```bash
export INSTANCE_ADDRESS=0x193491245A42d336ae5Fcb2d622d386041498a22
export INSTANCE_SERVICE_ADDRESS=<from instance registry / prior deploy notes>
# deploy adapted contracts from this repo; register product + new pool; create bundle with bundleLifetimeDays
```

Paste **new** product/pool addresses into the table below when deployed.

## ESF-1.03 – Amoy (test) – checklist

**Discovered 2026-11-23** (legacy product; adapted contracts not deployed yet):

| Item | Value |
|---|---|
| GIF instance | `0x193491245A42d336ae5Fcb2d622d386041498a22` |
| Registry | `0x7c19A25EF52c4E25Eb793d53B18F1811cE947455` |
| Legacy crop product | `0x6d39A6458ABa448d3C5cbC00f2135352197e6091` |
| Legacy accounting token | `0x612ef62560Ceb3b114fC302f7F54F4D493371D6B` |
| Product NFT id | `208000205` |
| Expired bundle (do not reuse) | `228000205` |

**Adapted deploy (2026-11-23, suffix `cdd740`)** — see `deployments/polygonAmoy/crop_deploy_cdd740.json`:

| Item | Value |
|---|---|
| Accounting token | `0x94671ab08d5940Da416168Fb7BD7646ed614059D` |
| Crop product | `0x20b1c9F88a7AaA4f7457e6f5aCAF05033e13229C` |
| Product NFT id | `378000205` |
| Crop pool | `0xAf64BA9DC3a90eca2d253dd6649064b01CFCE599` |
| Pool NFT id | `388000205` |
| Bundle | created (stake 1e12 units / 1M tokens); NFT id via explorer on pool `388000205` |

1. [x] Record GIF instance and registry addresses (reuse existing Amoy GIF v3).
2. [x] Deploy `AccountingToken` (LCA, 6 decimals).
3. [x] Deploy `CropProduct` + `CropPool` (+ authorization contracts) from this repo; link to instance.
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

## Dokku test cutover

**SSH:** `~/.ssh/config` hosts `esusfarm-dokku` (`dokku@`, key `~/.ssh/archive/dokku_deploy`) and `esusfarm-maint` (`maintenance@`).

```bash
git push esusfarm-dokku:esusfarm-api-test main:main
# or: git push dokku-test main:main
ssh esusfarm-maint dokku config:set esusfarm-api-test API_JWT_SECRET=<from issue_api_jwt.py>
ssh esusfarm-maint dokku config:set esusfarm-api-test RPC_NODE_URL=https://polygon-amoy-bor-rpc.publicnode.com
```

**Test Mongo** (URI is only reachable from the server): backup/dedupe via `scripts/mongo_backup_and_dedupe.py`, or one-off cleanup with `scripts/mongo_fix_test_external_id.py` inside the app container (`dokku run --no-tty esusfarm-api-test uv run python …`).

## API secrets (test)

| Variable | Purpose |
|---|---|
| `API_JWT_SECRET` | HS256 secret for fixed Bearer JWT (issue new value per env). |
| `API_JWT_ALGORITHM` | `HS256` (default). |

JWT is delivered to eSusFarm through a secure channel (not plain email).

See `docs/env.example` for variable names.

## Local mock deploy (Anvil only)

Unchanged: `forge script script/MockSetup.s.sol` deploys **mocks** under `src/mock/` for offline API dev without a full GIF instance.

## Prod (deferred)

See Implementation Plan ESF-1.11 after acceptance dry run and decisions D1–D3.