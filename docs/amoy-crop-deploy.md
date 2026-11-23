# ESF-1.03 – Deploy adapted crop on Amoy (reuse GIF instance)

## Target instance (discovered)

| Key | Value |
|---|---|
| Chain | Polygon Amoy (80002) |
| Registry | `0x7c19A25EF52c4E25Eb793d53B18F1811cE947455` |
| Instance | `0x193491245A42d336ae5Fcb2d622d386041498a22` |
| Instance NFT | `getNftId()` from legacy product (see `scripts/amoy_discover.py`) |
| Operator (deploy wallet) | `0xad8308964bcB8BfaCa77A625478D4D4E683CD433` |
| Legacy product (do not use for new policies) | `0x6d39A6458ABa448d3C5cbC00f2135352197e6091` |

## Prerequisites

1. **Operator mnemonic** (same as `esusfarm-api-test` `OPERATOR_WALLET_MNEMONIC`, index `OPERATOR_ACCOUNT_INDEX`, usually `2`).
2. **GIF library addresses** for release 3 on Amoy – either:
   - `lib/gif-next/deployments/polygonAmoy/libraries_80002.json` from the original GIF deploy, or
   - Run `deployLibraries` once via Hardhat (see below) and save the generated JSON.
3. **Node**: `npm ci` in `lib/gif-next` (Hardhat + typechain).
4. **RPC**: `https://polygon-amoy-bor-rpc.publicnode.com` (or other reliable Amoy endpoint).

## Differences vs gif-next example

eSusFarm contracts live under `src/crop/` (not `lib/gif-next/contracts/examples/crop/`):

- `CropProduct` – date checks removed (Q1).
- `CropPool` – extra constructor arg `bundleLifetimeDays_` (no hardcoded 90 days).

The stock `lib/gif-next/scripts/deploy_crop_components.ts` targets the **example** `CropPool` (4 constructor args). For production deploy either:

- Port that script to compile `src/crop` via a small Hardhat project in this repo, **or**
- Temporarily align the deploy script constructor args and `bundleLifetimeDays` (e.g. `180` days) when forking the TS script.

## Fast path: Forge script (this repo)

```bash
cp .env.deploy.local.example .env.deploy.local   # or auto-filled once from Dokku
chmod +x scripts/amoy_deploy.sh
SKIP_FORGE_BUILD=1 bash scripts/amoy_deploy.sh     # uses deployments/polygonAmoy/resume_*.env when present
```

Mnemonic in `.env.deploy.local` (gitignored) avoids SSH approval prompts. Token-registry txs use signer index **0**; product/pool use index **2**.

## Suggested Hardhat flow (gif-next)

```bash
cd lib/gif-next && npm ci

export NETWORK_URL=https://polygon-amoy-bor-rpc.publicnode.com
export WALLET_MNEMONIC='<operator mnemonic>'
export INSTANCE_ADDRESS=0x193491245A42d336ae5Fcb2d622d386041498a22
# populate from libraries_80002.json or after deployLibraries:
export AMOUNTLIB_ADDRESS=...
# ... (see deploy_crop_components.ts env block)

npx hardhat run scripts/deploy_crop_components.ts --network polygonAmoy
```

If libraries JSON is missing:

```bash
npx hardhat run scripts/deploy_gif.ts --network polygonAmoy  # only if standing up full GIF — not for reuse
# Prefer: extract libraries from prior deploy artifact or deploy libs only via a one-off script calling deployLibraries().
```

## After deploy

1. Fund new **AccountingToken** and create **bundle** on new **CropPool** (`createBundle` + stake).
2. Update Dokku **test only**:
   - `PRODUCT_CONTRACT_ADDRESS`
   - `TOKEN_CONTRACT_ADDRESS`
3. Copy ABIs: `forge build` then sync `out/CropProduct.sol/CropProduct.json` → `app/abi/CropProduct.sol/`.
4. `git push esusfarm-dokku:esusfarm-api-test main:main`
5. Run acceptance §3–5 in `docs/acceptance-test.md`.

## Verify

```bash
uv run python scripts/amoy_discover.py   # with PRODUCT_CONTRACT_ADDRESS set to new product
```

Polygonscan: [Amoy](https://amoy.polygonscan.com/)