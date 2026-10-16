#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
bash -n changelog.sh tests/test_changelog.sh
bash tests/test_changelog.sh
echo "VERIFIED: syntax and real-Git integration tests passed"
