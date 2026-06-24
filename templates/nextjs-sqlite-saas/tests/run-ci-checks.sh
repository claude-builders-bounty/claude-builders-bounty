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

on_err() {
  local exit_code=$?
  echo "template run-ci-checks failed: step exited with status ${exit_code} (line ${BASH_LINENO[0]})" >&2
  exit "$exit_code"
}
trap on_err ERR

run_step() {
  local label="$1"
  shift
  echo "==> ${label}"
  if ! "$@"; then
    echo "template run-ci-checks failed: ${label}" >&2
    exit 1
  fi
}

cd "$REPO_ROOT"

# Project-local temp dir avoids smoke-test and subprocess flakes when /tmp is cleared mid-run.
TEMPLATE_CACHE="${REPO_ROOT}/templates/nextjs-sqlite-saas/.cache"
mkdir -p "${TEMPLATE_CACHE}/tmp"
export TMPDIR="${TEMPLATE_CACHE}/tmp"

run_step "git merge-base" bash "${TESTS_DIR}/ci-step-git-base.sh"
run_step "security audits" bash "${TESTS_DIR}/ci-step-security.sh"
run_step "structural validation" bash "${TESTS_DIR}/ci-step-structural.sh"
run_step "reference app tests" bash "${TESTS_DIR}/ci-step-reference.sh"
run_step "delivery verification" bash "${TESTS_DIR}/ci-step-delivery.sh"
run_step "peer-review acceptance" bash "${TESTS_DIR}/ci-step-peer-review.sh"

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

run_step "attribution guard" bash "${TESTS_DIR}/ci-step-attribution.sh"

echo 'OK: all CI validation checks passed'
