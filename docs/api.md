# eSusFarm API (test / prod)

Base URL (test): `https://api-test.esusfarm.etherisc.com`  
OpenAPI: `/docs`

## Authentication

All routes except `/health/*` require:

```http
Authorization: Bearer <JWT>
```

JWT is HS256, issued per environment (`scripts/issue_api_jwt.py`). Secret: Dokku `API_JWT_SECRET` on the app.

## Policy sale (ESF-1.08)

```http
POST /policy
Content-Type: application/json
Authorization: Bearer …
```

```json
{
  "personId": "<nanoid>",
  "riskId": "<nanoid>",
  "externalId": "CLIENT-UNIQUE-ID",
  "subscriptionDate": "2019-06-14",
  "currency": "UGX",
  "sumInsuredAmount": 600000,
  "premiumAmount": 40000
}
```

- **UGX:** whole units only.
- **ZAR, NGN, USD, SZL:** up to 2 decimal places (format validation); **only UGX** is written on-chain today.
- Legacy numeric amounts without `currency` default to `UGX`.
- Creates Mongo record, syncs on-chain, returns `id`, `nft`, `tx` when successful.
- Same `externalId` + same payload → existing record (`200`).
- Same `externalId` + different payload → `409`.

## Idempotency

`externalId` is unique on **Person** and **Policy** (sparse index). Always send stable client ids.

## Health

```http
GET /health/ping
```

No authentication.

## Limits

Configurable via env (`POLICY_MAX_AMOUNT_*`). Default ceiling 5,000,000 per currency unless overridden.