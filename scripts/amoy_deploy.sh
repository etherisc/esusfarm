#!/usr/bin/env bash
# One-shot Amoy crop deploy wrapper: loads local secrets + optional resume env.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env.deploy.local ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env.deploy.local
  set +a
fi

if [[ -n "${AMOY_RESUME_ENV:-}" && -f "$AMOY_RESUME_ENV" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$AMOY_RESUME_ENV"
  set +a
fi

# Default resume file for in-progress cdd740 deploy
if [[ -z "${CROP_PRODUCT_ADDRESS:-}" && -f deployments/polygonAmoy/resume_cdd740.env ]]; then
  set -a
  # shellcheck disable=SC1091
  source deployments/polygonAmoy/resume_cdd740.env
  set +a
fi

export FOUNDRY_PROFILE="${FOUNDRY_PROFILE:-ci}"
exec uv run python scripts/amoy_deploy_crop.py "$@"