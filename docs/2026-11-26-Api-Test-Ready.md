# api-test ready — 2026-11-26

**Base URL:** `https://api-test.esusfarm.etherisc.com`  
**OpenAPI:** `/docs` · `/openapi.json`  
**JWT:** unchanged (existing test token remains valid)

## Deployed behaviour (this release)

1. **`currency` required** on `POST /policy` (Pydantic validation → 422 if missing).
2. **UGX only for on-chain** — non-UGX → **422** with  
   `only UGX policies are recorded on-chain on api-test`  
   **before** any Mongo insert (no partial policy row).
3. **UGX amount validation (api-test):** sum insured and premium each **1–5,000,000** whole units (`POLICY_MIN_AMOUNT_UGX` / `POLICY_MAX_AMOUNT_UGX`).
4. **On-chain product** `0x20b1…` **setConstants** updated to match **1–5,000,000** major units (6 decimals). Tx: `0x1ca7cc727c75d7f0be88c01b98fbbc90d75ca21984b3c1650458e8cc7d9c8cc3` (Amoy).

## Acceptance evidence

- Run fresh **UGX** E2E: `scripts/acceptance_api_test.sh` (new `accept-*` `externalId` each run).
- Pre-fix **USD** policy `accept-1795476889` — historical test only, not sign-off evidence.

## Reconciliation (23 Sep 2026 canaries)

See `docs/reconciliation/2026-09-23-canary-policies.md`.

## Production

Not in scope until joint api-test sign-off and separate prod limits from AIC.