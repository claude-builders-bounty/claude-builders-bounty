#!/usr/bin/env bash
# Root CI entry point for bounty #2 template validation.
#
# GitHub Actions (.github/workflows/test-nextjs-sqlite-template.yml) and local
# runners (`make test`, `npm test`) invoke this script. It delegates to the
# template-owned runner that delegates to focused ci-step-*.sh scripts:
#   1. ci-step-git-base.sh    — fetch merge-base for branch-diff attribution scans
#   2. ci-step-security.sh    — secret token + SQL parameterization audits
#   3. ci-step-structural.sh  — CLAUDE.md checks, validate-template, greenfield smoke
#   4. ci-step-reference.sh   — reference app ESLint + Vitest suites
#   5. ci-step-delivery.sh    — no_committed_diff + peer_review_not_passed gates
#   6. ci-step-peer-review.sh — bounty #2 acceptance criteria (peer review APPROVED)
#   7. ci-step-attribution.sh — reject agent trailers in sources/commits
#
# Keep orchestration here at repo root; keep template-specific logic under
# templates/nextjs-sqlite-saas/tests/ so greenfield copies stay self-contained.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_RUNNER="${REPO_ROOT}/templates/nextjs-sqlite-saas/tests/run-ci-checks.sh"

on_err() {
  local exit_code=$?
  echo "run-ci-checks failed: step exited with status ${exit_code} (line ${BASH_LINENO[0]})" >&2
  exit "$exit_code"
}
trap on_err ERR

if [[ ! -f "$TEMPLATE_RUNNER" ]]; then
  echo "run-ci-checks failed: missing template runner at ${TEMPLATE_RUNNER}" >&2
  exit 1
fi

if [[ ! -x "$TEMPLATE_RUNNER" ]]; then
  echo "run-ci-checks failed: template runner is not executable at ${TEMPLATE_RUNNER}" >&2
  exit 1
fi

echo "run-ci-checks: invoking template runner at ${TEMPLATE_RUNNER}" >&2
if ! bash "$TEMPLATE_RUNNER" "$@"; then
  exit_code=$?
  echo "run-ci-checks failed: template runner exited with status ${exit_code}" >&2
  exit "$exit_code"
fi
