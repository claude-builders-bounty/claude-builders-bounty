#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../pre-tool-use-blocker"
bash scripts/type-check.sh
