#!/usr/bin/env bash
# Peer-review acceptance suite for bounty #2 checklist.
set -euo pipefail

TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

peer_review_tests="$(
  grep -Ec '^\s*assert\(' "${TEMPLATE_DIR}/tests/peer-review-acceptance.test.mjs"
)"
node "${TEMPLATE_DIR}/tests/peer-review-acceptance.test.mjs"
echo "Ran ${peer_review_tests} tests — OK"
echo 'OK: peer review acceptance tests passed'
