#!/usr/bin/env bash
# Shared unittest runner for run-ci-checks.sh and package.json (avoids duplicated grep/run logic).
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: run-unittest-module.sh <module.py> <count_label> [ok_message...]" >&2
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODULE="$1"
COUNT_LABEL="$2"
shift 2

TEST_FILE="${REPO_ROOT}/${MODULE}"
if [[ ! -f "$TEST_FILE" ]]; then
  echo "missing test module: ${TEST_FILE}" >&2
  exit 1
fi

test_count="$(grep -Ec '^[[:space:]]*def test_' "$TEST_FILE")"
python3 -m unittest "$MODULE" -v
echo "Ran ${test_count} ${COUNT_LABEL} — OK"
for ok_message in "$@"; do
  echo "$ok_message"
done
