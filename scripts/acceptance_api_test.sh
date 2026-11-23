#!/usr/bin/env bash
# Quick api-test acceptance driver (§1–5). Requires API_JWT_SECRET on server or JWT env.
set -euo pipefail
BASE="${API_TEST_BASE:-https://api-test.esusfarm.etherisc.com}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -z "${API_TEST_JWT:-}" ]]; then
  SECRET=$(ssh -o BatchMode=yes esusfarm-maint 'dokku config:get esusfarm-api-test API_JWT_SECRET')
  API_TEST_JWT=$(cd "$ROOT" && uv run python scripts/issue_api_jwt.py --secret "$SECRET" 2>/dev/null | tail -1 | sed 's/^Bearer //')
fi
AUTH="Authorization: Bearer $API_TEST_JWT"

echo "§1 health"
curl -sS "$BASE/health/ping"
echo
echo "§2 auth"
curl -sS -o /dev/null -w "status=%{http_code}\n" "$BASE/policy/all/json"

echo "§3–5 flow"
EXT="accept-$(date +%s)"
LOC_ID=$(curl -sS -X POST "$BASE/location/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"country":"UG","zone":"Central","district":"MASAKA","subcounty":"T","village":"V","latitude":-0.43,"longitude":31.67,"coordinatesLevel":"VILLAGE"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
CFG_ID=$(curl -sS -X POST "$BASE/config/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"name":"Accept","startOfSeason":"2026-05-01","endOfSeason":"2026-10-01"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
RISK_ID=$(curl -sS -X POST "$BASE/risk/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"isValid\":true,\"configId\":\"$CFG_ID\",\"locationId\":\"$LOC_ID\",\"crop\":\"coffee\",\"startOfSeason\":\"2026-05-01\",\"endOfSeason\":\"2026-10-01\",\"deductible\":0}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
PER_ID=$(curl -sS -X POST "$BASE/person/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"locationId\":\"$LOC_ID\",\"externalId\":\"$EXT-p\",\"firstName\":\"A\",\"lastName\":\"B\",\"gender\":\"f\",\"mobilePhone\":\"+256700000099\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

BODY="{\"personId\":\"$PER_ID\",\"riskId\":\"$RISK_ID\",\"externalId\":\"$EXT\",\"subscriptionDate\":\"2026-05-10\",\"currency\":\"USD\",\"sumInsuredAmount\":600,\"premiumAmount\":2.01}"
curl -sS -w "\nHTTP:%{http_code}\n" -X POST "$BASE/policy/" -H "$AUTH" -H 'Content-Type: application/json' -d "$BODY"
curl -sS -w "\nrepeat:%{http_code}\n" -X POST "$BASE/policy/" -H "$AUTH" -H 'Content-Type: application/json' -d "$BODY"
curl -sS -w "\nconflict:%{http_code}\n" -X POST "$BASE/policy/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "${BODY/600/700}"