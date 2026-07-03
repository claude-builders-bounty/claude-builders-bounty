#!/usr/bin/env bash
# Delivery verification suite for fleet no_committed_diff gates.
# When invoked from full CI (npm test), skip nested npm test / test:peer-review
# recursion — isolated `npm run test:delivery` runs those E2E checks instead.
set -euo pipefail

TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

delivery_verification_tests="$(
  grep -Ec '^test\(' "${TEMPLATE_DIR}/tests/delivery-verification.test.mjs"
)"
export NEXTJS_TEMPLATE_CI_INNER_RUN=1
node "${TEMPLATE_DIR}/tests/delivery-verification.test.mjs"
echo "OK: no_committed_diff gate passed"
echo "OK: peer_review_not_passed gate passed"
echo "Ran ${delivery_verification_tests} delivery verification tests — OK"
echo "OK: delivery verification tests passed"
