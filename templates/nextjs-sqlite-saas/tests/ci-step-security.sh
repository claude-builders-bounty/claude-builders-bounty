#!/usr/bin/env bash
# Security audits — secret token exposure and SQL parameterization.
set -euo pipefail

TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

node "${TEMPLATE_DIR}/tests/check-secret-tokens.mjs"
node "${TEMPLATE_DIR}/tests/check-sql-parameterization.mjs"
