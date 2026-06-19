#!/usr/bin/env bash
# Reference app lint and Vitest suites.
set -euo pipefail

TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Running reference app unit and integration tests..."
bash "${TEMPLATE_DIR}/reference/scripts/run-tests.sh"
reference_app_tests="$(
  grep -rE '^\s*it\(' "${TEMPLATE_DIR}/reference/tests" \
    --include='*.test.ts' --include='*.test.tsx' 2>/dev/null | wc -l | tr -d ' '
)"
echo "Ran ${reference_app_tests} reference app tests — OK"
