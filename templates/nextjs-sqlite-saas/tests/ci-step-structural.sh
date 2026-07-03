#!/usr/bin/env bash
# Structural validation — CLAUDE.md conventions and greenfield smoke test.
set -euo pipefail

TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

node "${TEMPLATE_DIR}/tests/check-claude-md.mjs"
node "${TEMPLATE_DIR}/validate-template.mjs"
bash "${TEMPLATE_DIR}/tests/smoke-greenfield.sh"
