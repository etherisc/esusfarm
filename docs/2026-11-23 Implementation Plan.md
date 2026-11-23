# eSusFarm Uganda – Implementation Plan

| | |
|---|---|
| Date | 2026-11-23 |
| Basis | Offer AN20260004 v3 / Implementation Brief; Concept Questions |
| Scope now | **Test only** (`api-test` / Amoy). Production Dokku app and Polygon mainnet are **out of scope until dry run passes**. |
| Repo | `etherisc/esusfarm`, base branch `main` |

## 1. Goal for this phase

Bring **test** to a go-live-ready codebase on Amoy:

- Adapted Crop contracts in this repo, deployed against a **reused** GIF v3 instance on Amoy.
- API: Decimal amounts, JWT auth, date window removed, amount ceiling configurable, identifiers returned, idempotency, multi-currency **format** (UGX on-chain only).
- Joint acceptance prep and our dry run on `api-test`.
- **Do not** change `esusfarm-api` (prod) or mainnet until explicitly approved after dry run.

Live endpoints:

| Env | Dokku app | Public host | Host |
|---|---|---|---|
| Prod | `esusfarm-api` | `https://api.esusfarm.etherisc.com` | `162.55.209.69` — **leave alone** |
| Test | `esusfarm-api-test` | `https://api-test.esusfarm.etherisc.com` | same server |

## 2. Workstreams and order

```text
WS-A Contracts + GIF check     WS-B API features (parallel)
         │                              │
         ▼                              │
WS-C Amoy deploy (reuse GIF)            │
         │                              │
         └──────────┬───────────────────┘
                    ▼
         WS-D Wire api-test end-to-end
                    ▼
         WS-E Acceptance + dry run
                    ▼
         WS-F Production (later; not this phase)
```

Task IDs stay ESF-1.xx from the brief.

---

## 3. WS-A – Contracts and GIF version

### ESF-1.02 GIF version check
- Diff `v3.0.0-beta.3` vs current public GIF v3, limited to crop example + deploy surface.
- Record stay/upgrade in `docs/decisions.md`. Default: stay on beta.3 unless a blocking bug.

### ESF-1.01 Contract adaptation
1. Copy GIF crop example into this repo (replace mocks under `src/`): CropProduct, CropPool (+ authz if required), AccountingToken, shared Types as needed. Pin GIF core as submodule or documented dependency for compile.
2. Before removing checks: Forge test that GIF PolicyService accepts `activateAt` in the past; report result in evidence.
3. Changes:
   - Drop `activateAt < now` and `activateAt > seasonEndAt` in `createPolicy`.
   - Bundle lifetime/capacity: constructor or `createBundle` parameters (no hardcoded 90 days).
   - `createRisk` / `ErrorInvalidSeasonEndAt`: **drop** (Q1 = B).
4. Tests: recording after former 90-day window (time warp); past activateAt; property-style edge cases as feasible in Forge.
5. Regenerate `app/abi/` from the adapted contracts.

**Evidence:** test names + output, diff of removed checks.

---

## 4. WS-B – API (no chain required until end of stream)

Parallel PRs from `main` (or sequential if preferred). Each PR: pytest under ~1 min; no Amoy in PR CI.

| Task | Work |
|---|---|
| ESF-1.04 Decimal-safe amounts | `Decimal` end-to-end; exact 6-decimal conversion; property tests (`2.01` → `2010000`). |
| ESF-1.05 Authentication | Fixed Bearer JWT per env; all routes except health; **new** JWT (no OpenBao); secret in Dokku env only; remove Auth0/JWKS dead code; fix deps (`PyJWT`). |
| ESF-1.06 IP allowlist | Prod target `20.164.213.28/32` (later). **Test enforcement t.b.d.** Health stays open. Document Dokku/nginx vs app. |
| ESF-1.07 Date window + ceiling | Remove hardcoded 2024–2025; accept any valid `YYYY-MM-DD`; ceiling configurable (env/settings). |
| ESF-1.08 Identifiers | `POST /policy` auto-syncs on-chain (Q2 = A); response + read-back include API policy id, NFT id, tx hash. Keep sync for retry/force. |
| ESF-1.09 Idempotency | Unique index on `externalId` for person + policy; same data → existing; conflict → 409; **backup test Mongo, then** clean duplicates with removal list. |
| ESF-1.10 Multi-currency format | Mandatory `currency`; decimal strings; UGX integers; ZAR/NGN/USD/SZL ≤2 decimals; reject excess precision; per-currency ceiling; legacy numeric OK for Uganda; **only UGX wired on-chain**. |

**CI:** add Python unit job to GitHub Actions (fast). Keep Foundry job. Amoy e2e = manual/`workflow_dispatch` only.

---

## 5. WS-C – Amoy on-chain setup (test)

### ESF-1.03
1. **Locate existing GIF v3 on Amoy** via explorer from operator `0xad83…` / CropProduct `0x6d39…` (instance/registry). Prefer reuse over full GIF redeploy.
2. Deploy from this repo: Accounting Token “eSusFarm UGX” (6 decimals), adapted CropProduct, CropPool; register/link to that instance.
3. Create bundle with **parameterised** lifetime + capacity; fund with Accounting Tokens only.
4. Verify source on Polygon Amoy explorer.
5. Write mechanical steps + resulting addresses/bundle id/lifetime/capacity into `docs/deployment.md`.
6. Point `esusfarm-api-test` env at new product/token/RPC (Dokku config); do **not** change prod config.

**Evidence:** explorer links, verified source, bundle metadata.

**Fallback:** if no usable Amoy GIF instance is found, stop and escalate (Christoph) before deploying a new GIF instance.

---

## 6. WS-D – Wire `api-test` end-to-end

1. Deploy API build that includes WS-B + new ABIs to **`esusfarm-api-test` only** (`git push dokku-test …`).
2. Smoke: health (no auth) → authenticated create → on-chain record → read-back NFT + tx on explorer.
3. Fix float/Decimal path in `sync/policy.py` (and risk `to_u_fixed` if in scope for amounts).
4. JWT secret and RPC key: Dokku env only (no OpenBao); document env var names in `deployment.md` (no secrets in git). Issue a new test JWT when ESF-1.05 lands.

**Prod backup / empty DB / mainnet (ESF-1.11):** deferred. Do not drop or rewrite prod DB in this phase.

---

## 7. WS-E – Acceptance and dry run

### ESF-1.12
1. Write `docs/acceptance-test.md`: auth, allowlist intent, E2E policy→chain, identifier read-back, 409, two-decimal amounts.
2. Reconcile `api-test` records from **2026-09-23**: table of id / on-chain? / tx or reason missing.
3. Internal dry run; then hand off summary for eSusFarm (endpoints, JWT delivery via secure channel, known limitations).

---

## 8. WS-F – Production (explicit later gate)

Only after dry run + D1/D2/D3 approvals:

- Backup prod Mongo; D2 before any wipe.
- Same codebase as test; mainnet deploy analogous to ESF-1.03; IP allowlist `20.164.213.28/32`; rotate RPC (D3); new operator wallet + POL (D1).

**Not started in this phase.**

---

## 9. Docs to produce (Markdown)

| File | Content |
|---|---|
| `docs/decisions.md` | Decision log (GIF version, Q1, Q2, deploy choices). |
| `docs/deployment.md` | Mechanical Amoy (then later mainnet) runbook. |
| `docs/api.md` | Client-facing API. |
| `docs/acceptance-test.md` | Script + results. |
| `docs/2026-11-23 Concept Questions.md` | Open product questions (existing). |

---

## 10. Git / review workflow

1. Update local `main` from `origin/main`.
2. Worktree or branch from `main` → feature branch → PR → merge after **non-author** review → delete worktree/branch.
3. Deploy test via `dokku-test` remote only.
4. Status posts: task start / done+evidence / blocked (coordination thread; German for messages).

---

## 11. Testing strategy

| Layer | What | When |
|---|---|---|
| Forge | Contract rules, past activateAt, bundle lifetime param, time warp past 90d | Every contract PR |
| Pytest | Decimal conversion, JWT 401, dates, ceiling, idempotent 200/409, currency validation | Every API PR (&lt;1 min) |
| Manual Amoy | Deploy + one policy E2E + explorer proof | After WS-C/D; `workflow_dispatch` optional |
| Acceptance | Script in `acceptance-test.md` + reconciliation table | WS-E |
| Prod | None in this phase | — |

---

## 12. Risks and dependencies

| Risk | Mitigation |
|---|---|
| No reusable GIF on Amoy | Escalate; do not improvise full GIF deploy without approval |
| Q1 / Q2 | Decided: drop risk date check; auto on-chain on create |
| Test DB duplicates | ESF-1.09 cleanup list before unique index |
| Legacy Brownie scripts | Ignore for v3; new Foundry (or documented) deploy path only |
| Prod accidental push | Never push `dokku` remote in this phase; checklist in deployment.md |

---

## 13. Suggested first PRs

1. **docs + plan** (this file, concept questions) — optional.
2. **ESF-1.02** decision note.
3. **Vendor + adapt contracts** (ESF-1.01) once Q1 known or with risk check deferred.
4. **API Decimal + dates + JWT** (can combine or split).
5. **Idempotency + currency format**.
6. **Amoy deploy runbook + addresses** then **api-test** cutover.

Time: track actual hours per ESF-1.xx; flag &gt;20% over estimate early (esp. 2.1 / 2.2 billed).
