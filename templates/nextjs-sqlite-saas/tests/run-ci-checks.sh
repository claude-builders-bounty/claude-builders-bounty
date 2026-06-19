#!/usr/bin/env bash
# Template CI runner — invoked by scripts/run-ci-checks.sh at repo root.
#
# Orchestrates focused step scripts (each individually runnable for debugging):
#   ci-step-git-base.sh       — fetch merge-base for branch-diff attribution scans
#   ci-step-security.sh       — secret token + SQL parameterization audits
#   ci-step-structural.sh     — CLAUDE.md checks, validate-template, greenfield smoke
#   ci-step-reference.sh      — reference app lint + Vitest suites
#   ci-step-delivery.sh       — delivery verification suite
#   ci-step-peer-review.sh    — peer-review acceptance suite
#   ci-step-attribution.sh    — reject agent trailers in sources/commits
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$REPO_ROOT"

bash "${TESTS_DIR}/ci-step-git-base.sh"
bash "${TESTS_DIR}/ci-step-security.sh"
bash "${TESTS_DIR}/ci-step-structural.sh"
bash "${TESTS_DIR}/ci-step-reference.sh"
bash "${TESTS_DIR}/ci-step-delivery.sh"
bash "${TESTS_DIR}/ci-step-peer-review.sh"

delivery_verification_tests="$(
  grep -Ec '^test\(' "${TESTS_DIR}/delivery-verification.test.mjs"
)"
peer_review_tests="$(
  grep -Ec '^\s*assert\(' "${TESTS_DIR}/peer-review-acceptance.test.mjs"
)"
reference_app_tests="$(
  grep -rE '^\s*it\(' "${REPO_ROOT}/templates/nextjs-sqlite-saas/reference/tests" \
    --include='*.test.ts' --include='*.test.tsx' 2>/dev/null | wc -l | tr -d ' '
)"
total_tests=$((delivery_verification_tests + peer_review_tests + reference_app_tests))
echo "OK: ${total_tests} tests passed"

bash "${TESTS_DIR}/ci-step-attribution.sh"

echo 'OK: all CI validation checks passed'
