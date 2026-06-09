#!/usr/bin/env bash
# Root CI entry point for bounty #2 template validation.
#
# GitHub Actions (.github/workflows/test-nextjs-sqlite-template.yml) and local
# runners (`make test`, `npm test`) invoke this script. It delegates to the
# template-owned runner that contains the actual validation steps:
#   1. Structural CLAUDE.md validation (validate-template.mjs)
#   2. Greenfield smoke test (create-next-app@15 scaffold)
#   3. Delivery verification suite (npm wiring, CI summaries)
#   4. Peer-review acceptance suite (bounty checklist codified)
#   5. Attribution guard (no agent trailers in template or commits)
#
# Keep orchestration here at repo root; keep template-specific logic under
# templates/nextjs-sqlite-saas/tests/ so greenfield copies stay self-contained.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_RUNNER="${REPO_ROOT}/templates/nextjs-sqlite-saas/tests/run-ci-checks.sh"

if [[ ! -x "$TEMPLATE_RUNNER" ]]; then
  echo "run-ci-checks failed: missing executable template runner at ${TEMPLATE_RUNNER}" >&2
  exit 1
fi

exec bash "$TEMPLATE_RUNNER" "$@"
