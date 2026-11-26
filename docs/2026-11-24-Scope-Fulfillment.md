# eSusFarm Global – Scope fulfillment document

| | |
|---|---|
| **Prepared for** | eSusFarm Africa |
| **Prepared by** | Etherisc GmbH |
| **Scope reference** | [2026-10-14 Etherisc-eSusFarm-Scope.pdf](./2026-10-14%20Etherisc-eSusFarm-Scope.pdf) (Offer AN20260004) |
| **Approved scope** | **Part 1** (§1.1–§1.9) · **Part 2.1** (duplicate prevention) · **Part 2.2** (multi-currency format) |
| **Document date** | 2026-11-24 |
| **Environment covered here** | **Test** (`https://api-test.esusfarm.etherisc.com`, Polygon Amoy chain id `80002`) |
| **Repository / release** | `etherisc/esusfarm` `main` (merge PR #17, `b8b1b36`) |

This document is the **fulfillment record** for the approved scope: what was delivered, how eSusFarm uses it, and how eSusFarm can **systematically test** each obligation. It does not replace the commercial scope PDF; it maps that PDF to the running test system.

---

## 1. Confidentiality and exclusions

- Treat contract addresses, JWTs, and mnemonics as **confidential** (JWT via secure channel only).
- **Not included** (per scope PDF §6): Polygon **gas** on mainnet, recurring **operation / maintenance / support**, **Part 3** (claims, payouts, real risk capital, loan events), **Part 2.3 / 2.4** (currency routing and additional on-chain currencies), **Part 1.10** `add_payment` (later release).
- **Production** API (`https://api.esusfarm.etherisc.com`) and **Polygon mainnet** UGX stack are **deferred** until joint acceptance on api-test is signed off (Part 1.1 / 1.7 prod).

---

## 2. How policy sale recording works (scope §1)

Aligned with the scope PDF “Flow of one policy sale”:

1. **Authenticate** with the fixed Bearer JWT for the environment.
2. **Submit master data**: location → config (season) → risk → person → **policy**.
3. The API creates a **farmer on-chain wallet**, credits **Accounting Tokens** (bookkeeping only; no real money on-chain).
4. The API calls **CropProduct** to validate inputs and **create the policy** in GIF v3.
5. GIF records sum insured against the **bundle**, activates the policy, and books premium in Accounting Tokens (bookkeeping only).
6. The API returns **policy id** (API), **nft** (on-chain policy NFT id), and **tx** (transaction hash).

**On-chain stack (test / UGX):**

| Component | Role |
|-----------|------|
| Accounting Token “Local Currency Accounting” (6 decimals) | Internal unit of account for amounts |
| CropProduct | Seasons, locations, crops, risks, policies |
| CropPool + bundle | GIF-backed record of aggregate policies (staked Accounting Tokens only) |
| REST API | Persistence + orchestration + identifiers |

---

## 3. Scope fulfillment matrix

Status for the **approved** scope on **api-test** as of this document.

| Scope ref | Title | Fulfillment (test) | Evidence / notes |
|-----------|--------|-------------------|------------------|
| **1.1** | Production on current codebase | **Deferred** | Test host on current code; prod cutover not executed |
| **1.2** | Fixed Bearer JWT | **Fulfilled** | `API_JWT_SECRET` on Dokku; `app/server/auth.py`; health open |
| **1.3** | IP allowlist `20.164.213.28/32` | **Deferred (prod)** | Not enforced on api-test; prod rule documented in `docs/decisions.md` |
| **1.4** | Subscription date | **Fulfilled** | Any valid `YYYY-MM-DD`; past dates accepted; adapted contracts on Amoy |
| **1.5** | Configurable amount ceiling | **Fulfilled** | `POLICY_MAX_AMOUNT_*` env settings |
| **1.6** | Decimal-safe amounts | **Fulfilled** | `util/money.py`; unit tests (`2.01` → `2_010_000` base units) |
| **1.7** | On-chain setup UGX (test) | **Fulfilled** | Deploy record `deployments/polygonAmoy/crop_deploy_cdd740.json`; bundle lifetime **180 days** |
| **1.7** | On-chain setup UGX (prod) | **Deferred** | Mainnet deploy not in this phase |
| **1.8** | Recording and identifiers | **Fulfilled** | `POST /policy/` returns `id`, `nft`, `tx`; `GET /policy/{id}` read-back |
| **1.9** | Acceptance test | **In progress** | This document + §7 test plan; Sep-2026 reconciliation sheet for eSusFarm to complete |
| **1.10** | `add_payment` | **Out of release** | Awaiting eSusFarm specification |
| **2.1** | Duplicate prevention | **Fulfilled** | Person + policy `externalId`; 409 on conflict; Mongo indexes |
| **2.2** | Multi-currency format | **Fulfilled (API)** | `currency` + validation UGX/ZAR/NGN/USD/SZL; **on-chain still single UGX product** |

---

## 4. Test environment reference

### 4.1 Endpoints

| Purpose | URL |
|---------|-----|
| API base (test) | `https://api-test.esusfarm.etherisc.com` |
| OpenAPI (Swagger) | `https://api-test.esusfarm.etherisc.com/docs` |
| Health (no auth) | `GET /health/ping` |
| Amoy explorer | [https://amoy.polygonscan.com/](https://amoy.polygonscan.com/) |

### 4.2 On-chain addresses (Amoy, deploy suffix `cdd740`)

| Item | Address / id |
|------|----------------|
| Chain | Polygon Amoy (`80002`) |
| GIF instance | `0x193491245A42d336ae5Fcb2d622d386041498a22` |
| Registry | `0x7c19A25EF52c4E25Eb793d53B18F1811cE947455` |
| Accounting token | `0x94671ab08d5940Da416168Fb7BD7646ed614059D` |
| Crop product | `0x20b1c9F88a7AaA4f7457e6f5aCAF05033e13229C` |
| Crop pool | `0xAf64BA9DC3a90eca2d253dd6649064b01CFCE599` |
| Product NFT id | `378000205` |
| Pool NFT id | `388000205` |
| Bundle lifetime | 180 days (constructor parameter) |

Full machine-readable record: `deployments/polygonAmoy/crop_deploy_cdd740.json`.

### 4.3 On-chain policy limits (CropProduct constants)

Amounts on-chain use **6 decimals** on the Accounting Token (same scale as API conversion for recording).

| Limit | Typical value (major units) | Base units (6 decimals) |
|-------|----------------------------|---------------------------|
| Minimum premium | 10 | `10_000_000` |
| Minimum sum insured | 200 | `200_000_000` |
| Maximum sum insured | 1_000 | `1_000_000_000` |

Use **premium ≥ 10** and **sum insured between 200 and 1000** in acceptance tests unless ceilings in §5.3 are stricter.

### 4.4 API amount ceilings (configurable)

Default **5_000_000** per currency unless Dokku overrides (`POLICY_MAX_AMOUNT_UGX`, etc.). Policy validation uses the **currency** field to select the ceiling.

---

## 5. User guide – new and changed behaviour

### 5.1 Authentication (Part 1.2)

Every request **except** `/health/*` must include:

```http
Authorization: Bearer <JWT>
```

- Algorithm: **HS256**
- Secret: server env `API_JWT_SECRET` (set by Etherisc on Dokku; **rotating** the secret invalidates old tokens)
- Etherisc delivers a **test JWT** to eSusFarm through a **secure channel** (not email)

**Check:** `GET /policy/all/json` without header → **401**. With valid JWT → **200**.

### 5.2 Policy sale sequence (Part 1.8)

Create entities in order (each step needs the JWT):

| Step | Method | Path | Purpose |
|------|--------|------|---------|
| 1 | `POST` | `/location/` | Geographic master data |
| 2 | `POST` | `/config/` | Season (start/end, name) |
| 3 | `POST` | `/risk/` | Links config + location + crop |
| 4 | `POST` | `/person/` | Farmer; optional `externalId` for idempotency |
| 5 | `POST` | `/policy/` | **Records policy on-chain**; returns identifiers |

**Policy body (example – Uganda, on-chain path):**

```json
{
  "personId": "<from step 4>",
  "riskId": "<from step 3>",
  "externalId": "ESF-POL-2026-00042",
  "subscriptionDate": "2019-06-14",
  "currency": "UGX",
  "sumInsuredAmount": 600000,
  "premiumAmount": 40000
}
```

**Successful response fields (Part 1.8):**

| Field | Meaning |
|-------|---------|
| `id` | API policy identifier (nanoid) |
| `nft` | GIF policy NFT id on Polygon |
| `tx` | Transaction hash of `createPolicy` |
| `externalId` | Your stable business key |

**Read-back:** `GET /policy/{id}` — same `nft` and `tx`.

**Explorer:** open `https://amoy.polygonscan.com/tx/{tx}` and confirm success; contract `0x20b1c9F88a7AaA4f7457e6f5aCAF05033e13229C`.

**Timing:** First policy for a new person triggers token funding and farmer approval; allow **~15–30 seconds** before expecting `nft` and `tx`.

### 5.3 Subscription date (Part 1.4)

- Send any valid ISO date `YYYY-MM-DD` (including **past** dates).
- Stored and passed to chain **unchanged** (no 2024–2025 window).

### 5.4 Amounts and decimals (Part 1.5, 1.6, 2.2)

| Topic | Behaviour |
|-------|-----------|
| **UGX** | Whole units only; fractional UGX rejected |
| **ZAR, NGN, USD, SZL** | Up to **2** decimal places; excess precision **rejected** (not rounded) |
| **Conversion** | API converts major units → token **base units** with exact 6-decimal arithmetic (e.g. `2.01` → `2_010_000`) |
| **Default currency** | **`currency` is required** on `POST /policy` (no default) |
| **On-chain write (api-test)** | **UGX only** — other currencies → **422** before Mongo write (until Part 2.3/2.4) |
| **api-test UGX bounds** | Sum insured and premium each **1–5,000,000** whole units (technical test limits) |
| **Ceiling** | Per-currency max via `POLICY_MAX_AMOUNT_*` |

**Example – two-decimal premium (format test, USD):**

```json
"currency": "USD",
"sumInsuredAmount": 200,
"premiumAmount": 2.01
```

For a **successful on-chain** create in test, respect **§4.3** minima (e.g. premium ≥ 10, sum insured ≥ 200).

### 5.5 Duplicate prevention (Part 2.1)

| Entity | Idempotency key | Same key + same data | Same key + different data |
|--------|-----------------|----------------------|-------------------------|
| **Person** | `externalId` (optional but recommended) | **200**, same record | **409** |
| **Policy** | `externalId` **required** | **200**, same record; **retries on-chain** if first attempt left `tx` empty | **409** |
| Location, config, risk | — | Normal create (no `externalId` rule) | Master data; manage duplicates in your process |

**Policy idempotent payload** compares: `personId`, `riskId`, `subscriptionDate`, `currency`, `sumInsuredAmount`, `premiumAmount` (normalized decimals).

**Recommendation:** Use **globally unique** `externalId` per policy and per person across environments you control.

### 5.6 Retry and manual sync

If a policy row exists without `tx` (e.g. transient chain error), **repeat the same `POST /policy/`** with the same `externalId` and body — the API **retries on-chain sync**.

Manual operator retry (authenticated):

```http
POST /policy/{policy_id}/sync
POST /policy/{policy_id}/sync:force
```

### 5.7 What is unchanged / not available

- **Claims, payouts, processing** API paths exist for legacy data but **Uganda scope does not include** triggering claims/payouts (Part 3).
- **Production IP allowlist** not active on api-test.
- **Separate CropProduct per currency** not deployed (Part 2.3 / 2.4).

---

## 6. Error handling quick reference

| HTTP | Typical cause |
|------|----------------|
| **401** | Missing/invalid JWT |
| **409** | `externalId` already used with different payload |
| **422** | Validation (nanoid, date, currency, decimals, ceiling) |
| **500** | On-chain revert (limits, gas, bundle, etc.) — note `tx` in logs; retry per §5.6 |

---

## 7. Systematic test plan (eSusFarm)

Use this checklist for **joint acceptance (Part 1.9)**. Record **Pass / Fail**, **tester**, **date**, and **notes** on each row.

### 7.0 Prerequisites

| # | Action | Pass? |
|---|--------|-------|
| P1 | Receive **test JWT** via secure channel | |
| P2 | Confirm api-test URL reachable | |
| P3 | Optional: read OpenAPI at `/docs` | |

### 7.1 Connectivity and auth (scope §5 acceptance + 1.2)

| ID | Test | Steps | Expected |
|----|------|-------|----------|
| T-01 | Health | `GET /health/ping` | `{"response":"OK"}` |
| T-02 | Auth required | `GET /policy/all/json` without JWT | **401** |
| T-03 | Auth success | Same with `Authorization: Bearer …` | **200** |

### 7.2 End-to-end policy recording (scope 1.8, flow §1)

| ID | Test | Steps | Expected |
|----|------|-------|----------|
| T-10 | Full sale | Create location → config → risk → person → policy (UGX, past `subscriptionDate`, amounts meeting §4.3) | **200**; body has non-null `id`, `nft`, `tx` |
| T-11 | Read-back | `GET /policy/{id}` | Same `nft`, `tx` |
| T-12 | Explorer | Open Amoy Polygonscan for `tx` | Status success; interacts with product `0x20b1…` |
| T-13 | Past subscription | Repeat T-10 with `subscriptionDate` in the past (e.g. `2019-06-14`) | **200**; on-chain record created |

**Example curl chain:** see `scripts/acceptance_api_test.sh` (Etherisc smoke script). Replace JWT and use your own `externalId` values.

### 7.3 Duplicate prevention (Part 2.1)

| ID | Test | Steps | Expected |
|----|------|-------|----------|
| T-20 | Policy idempotent | `POST /policy/` twice, same `externalId` + body | Both **200**; same `id`, `nft`, `tx` |
| T-21 | Policy conflict | Same `externalId`, change e.g. `premiumAmount` | **409** |
| T-22 | Person idempotent | `POST /person/` twice, same `externalId` + same person fields | **200**; same `id` |
| T-23 | Person conflict | Same `externalId`, different `mobilePhone` | **409** |

### 7.4 Multi-currency format (Part 2.2)

| ID | Test | Steps | Expected |
|----|------|-------|----------|
| T-30 | UGX integer | `currency":"UGX"`, `premiumAmount": 40000` | **200** (if on-chain limits met) |
| T-31 | UGX reject fraction | `premiumAmount": 40000.5` | **422** (or validation error) |
| T-32 | USD two decimals | `"currency":"USD"`, `"premiumAmount":"2.01"` | **200** or validation **422** if below on-chain min premium |
| T-33 | USD reject precision | `"premiumAmount":"2.019"` | **422** |
| T-34 | Unsupported currency | `"currency":"EUR"` | **422** |
| T-35 | Ceiling | Sum insured above `POLICY_MAX_AMOUNT_UGX` | **422** |

### 7.5 Decimal exactness (Part 1.6)

| ID | Test | Steps | Expected |
|----|------|-------|----------|
| T-40 | Two-decimal premium | Policy with `premiumAmount` **10.01** (and sum insured ≥ 200) | On-chain premium units = **10_010_000** (verify via explorer “Input Data” or internal tooling) |

### 7.6 Historical reconciliation (Part 1.9)

Reconcile policies created on **2026-09-23** on api-test (eSusFarm holds the business list).

| API policy `id` / `externalId` | On-chain (`nft` + `tx` present?) | Notes |
|-------------------------------|----------------------------------|-------|
| | | |
| | | |

*Etherisc can supply Mongo export on request for the test database.*

### 7.7 Automated smoke (optional)

If eSusFarm has VPN/SSH to issue JWT from Dokku, Etherisc’s script runs sections analogous to T-01–T-21:

```bash
export API_TEST_JWT='<token-from-secure-channel>'
export API_TEST_BASE='https://api-test.esusfarm.etherisc.com'
./scripts/acceptance_api_test.sh
```

Expected: health OK; auth 401; policy flow **200** with `nft`/`tx`; repeat **200**; conflict **409**.

### 7.8 Sign-off

| Role | Name | Date | Signature / approval |
|------|------|------|----------------------|
| eSusFarm technical | | | |
| eSusFarm business | | | |
| Etherisc | | | |

**Sign-off criteria (approved scope on api-test):** T-01–T-03, T-10–T-13, T-20–T-23, T-30–T-35, T-40 passed; reconciliation sheet completed or agreed; limitations in §8 accepted.

---

## 8. Known limitations and next phases

| Item | Status |
|------|--------|
| Production API + empty/migrated DB (1.1) | Planned after acceptance |
| Mainnet UGX deploy (1.7 prod) | Planned after acceptance |
| Prod IP allowlist (1.3) | To implement with prod go-live |
| Currency routing + extra currencies (2.3, 2.4) | Not ordered |
| Claims / payouts / real pools (Part 3) | Not in scope |
| `add_payment` (1.10) | Awaiting specification |
| Polygonscan **verified source** for all contracts | In progress; addresses fixed in §4.2 |

---

## 9. Related repository documentation

| Document | Content |
|----------|---------|
| [docs/api.md](./api.md) | Short API reference |
| [docs/acceptance-test.md](./acceptance-test.md) | Etherisc internal acceptance checklist |
| [docs/deployment.md](./deployment.md) | Amoy deploy checklist, Dokku env names |
| [docs/amoy-crop-deploy.md](./amoy-crop-deploy.md) | Operator deploy runbook |
| [docs/decisions.md](./decisions.md) | Architecture decisions (JWT, dates, GIF reuse) |
| [docs/env.example](./env.example) | Non-secret env variable names |

---

## 10. Document control

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-11-24 | Initial fulfillment doc for approved Part 1 + 2.1 + 2.2 (api-test) |

**Contact:** Etherisc project team for JWT rotation, reconciliation exports, and prod cutover planning.

---

*Basis: Etherisc scope PDF 2026-10-14; implementation on `etherisc/esusfarm` main; api-test Dokku deploy includes policy sync and gas-limit fixes (PR #17).*