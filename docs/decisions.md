# eSusFarm – Decision log

Short record of implementation choices. Newest entries first.

---

## D-2026-11-23-09 – Test IP allowlist

**Context:** ESF-1.06 prod rule is `20.164.213.28/32`.  
**Status:** Open (t.b.d. whether test enforces any allowlist).  
**Choice:** —

---

## D-2026-11-23-08 – JWT storage

**Context:** ESF-1.05 requires a rotatable Bearer JWT without code changes.  
**Options:** OpenBao vs Dokku env.  
**Choice:** **Dokku env** (no OpenBao on this project). New JWT issued per environment.

---

## D-2026-11-23-07 – Policy create flow

**Context:** See `docs/2026-11-23 Concept Questions.md` Q2.  
**Choice:** **A** – `POST /policy` persists and writes on-chain in one request; response includes NFT id and tx hash.

---

## D-2026-11-23-06 – Risk `seasonEndAt` wall-clock check

**Context:** See Concept Questions Q1.  
**Choice:** **B** – remove `ErrorInvalidSeasonEndAt` on `createRisk` and policy activation date wall-clock checks (ESF-1.01).

---

## D-2026-11-23-05 – Amoy GIF instance

**Context:** ESF-1.03 deploy cost and repeatability.  
**Choice:** **Reuse** existing GIF v3 on Polygon Amoy; discover instance/registry via explorer from operator `0xad8308964bcB8BfaCa77A625478D4D4E683CD433` and prior CropProduct `0x6d39A6458ABa448d3C5cbC00f2135352197e6091`.

---

## D-2026-11-23-04 – Git workflow

**Context:** Implementation brief mentioned `develop`.  
**Choice:** **`main`** is default integration branch; feature branches from `main`, PR merge to `main`.

---

## D-2026-11-23-03 – Contract source of truth

**Context:** Repo had Foundry mocks; production ABIs are GIF v3 crop.  
**Choice:** **All eSusFarm contracts in this repo** – `lib/gif-next` submodule (pinned), adapted crop contracts under `src/crop/`.

---

## D-2026-11-23-02 – GIF version (ESF-1.02)

**Context:** Brief baseline `v3.0.0-beta.3` (commit `4f4b737`).  
**Evidence:** Public GitHub releases for `etherisc/gif-next` list **no tag newer than `v3.0.0-beta.3`** (2024). Local `gif-next` default branch has moved forward but no newer **released** v3 tag affects a formal upgrade decision.  
**Options:** Stay on beta.3 vs track `main`.  
**Choice:** **Stay on `v3.0.0-beta.3`** submodule pin until a newer release or blocking bug on `main` is documented. Re-check before mainnet (ESF-1.11).

---

## D-2026-11-23-01 – Production in phase 1

**Context:** Live prod at `api.esusfarm.etherisc.com`.  
**Choice:** **No prod Dokku or mainnet changes** until acceptance dry run on `api-test.esusfarm.etherisc.com` passes.