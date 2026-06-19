#!/usr/bin/env bash
# Delivery verification suite for fleet no_committed_diff gates.
set -euo pipefail

TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

delivery_verification_tests="$(
  grep -Ec '^test\(' "${TEMPLATE_DIR}/tests/delivery-verification.test.mjs"
)"
node "${TEMPLATE_DIR}/tests/delivery-verification.test.mjs"
echo "Ran ${delivery_verification_tests} delivery verification tests — OK"
