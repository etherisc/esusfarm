# eSusFarm – Concept Questions

| | |
|---|---|
| Date | 2026-11-23 |
| Status | Q1 and Q2 decided (2026-11-23) |
| Related | Implementation Brief ESF-1.01 / ESF-1.08; Implementation Plan |

---

## Q1 – Past season end when creating a risk on-chain

### Problem

GIF CropProduct currently rejects creating a risk whose season end is already in the past:

- `createRisk(... seasonEndAt)` reverts with `ErrorInvalidSeasonEndAt` if `seasonEndAt < block.timestamp`.

Separately, creating a policy rejects an activation time in the past or after the season end (`ErrorInvalidActivateAt`). The implementation brief already plans to remove those **policy** date checks so historical subscription dates can be recorded on-chain for audit.

If only the policy checks are removed and the **risk** check stays:

- Syncing a risk for a season that has already ended still fails.
- Replaying or backfilling older seasons (or re-running acceptance data after the season window) remains blocked, even though policy dates would be allowed.

`seasonEndAt` would still be stored and still used for policy lifetime calculation; the only question is whether wall-clock may reject risk creation.

### Options

| Option | Behaviour |
|---|---|
| **A – Keep the risk check** | Risks may only be created while `seasonEndAt` is still in the future. Past seasons cannot be synced on-chain. Simpler product rule; backfill needs workarounds. |
| **B – Drop the risk check (recommended)** | No on-chain date rule on risk or policy creation. Any valid season/risk can be recorded; audit and backfill work. Season metadata and lifetime logic stay unchanged. |

### Recommendation

**Option B.** Align with the brief’s intent that recording is for auditability of sales (including past subscription dates), not for enforcing a live sales window on-chain. Sales windows belong in the API/config if needed later—not in GIF for this go-live.

### Decision

**B** (2026-11-23, Christoph). ESF-1.01 drops the `createRisk` season-end wall-clock check together with the policy date checks.

---

## Q2 – Policy create vs on-chain write

### Problem

Today `POST /policy` only writes MongoDB; on-chain recording is a separate `POST /policy/{id}/sync`. The brief says each sale is written on-chain and the create response includes policy id, NFT id, and tx hash.

### Options

| Option | Behaviour |
|---|---|
| **A – Auto on create** | `POST /policy` persists and syncs on-chain in one request; response includes NFT id + tx. Sync endpoint optional (retry/force). |
| **B – Keep two-step** | Create stays off-chain; client (or operator) must call sync; identifiers appear after sync. Acceptance script must cover both calls. |

### Recommendation

**A**, so a successful sale API call always means an on-chain record (matches audit goal and brief wording).

### Decision

**A** (2026-11-23, Christoph). `POST /policy` writes MongoDB and on-chain in one request; response includes NFT id and tx hash. Sync endpoint may remain for retry/force.

---

## Settled (for the record)

| Topic | Decision |
|---|---|
| Git base branch | Keep `main` as default. |
| Contract ownership | All eSusFarm contracts live in this repo (copy from GIF crop example if needed, then adapt here). |
| Authentication | Fixed Bearer JWT per environment; remove unused Auth0/JWKS code. |
| Amoy GIF instance | Prefer reusing an existing GIF v3 deployment on Polygon Amoy; deploy adapted CropProduct / CropPool / Accounting Token and bundle against it. |
| Bundle lifetime / capacity | Deployment parameters (not hardcoded 90 days). Document addresses, verification, bundle ID, lifetime and capacity. |
| Documentation format | Plain Markdown under `docs/`. Publishing strategy later. |
| Prod in this phase | Do not touch prod Dokku app or mainnet until dry run on test passes. |
| Q1 Risk season-end check | **B** – drop on-chain wall-clock check on `createRisk`. |
| Q2 Policy create vs sync | **A** – auto on-chain on `POST /policy`. |
| Test URL | `https://api-test.esusfarm.etherisc.com` → Dokku `esusfarm-api-test` on `162.55.209.69` (same host as prod). |
| Amoy GIF discovery | Discover via explorer / operator wallet `0xad8308964bcB8BfaCa77A625478D4D4E683CD433` (and known CropProduct `0x6d39A6458ABa448d3C5cbC00f2135352197e6091`). |
| Test DB duplicates (ESF-1.09) | Backup test Mongo first, then clean up; keep a list of what was removed. |
| JWT / secrets | No OpenBao on this project. Issue a **new** fixed JWT for test (and later prod); store via Dokku env / secure channel only. |
| IP allowlist on test (ESF-1.06) | Still open (t.b.d.). Prod rule remains `20.164.213.28/32` when prod is in scope. |
