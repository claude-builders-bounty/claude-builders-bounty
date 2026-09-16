#!/usr/bin/env bash
# Structured CHANGELOG Generator from Git History
# Fulfills Bounty #1 on claude-builders-bounty

set -eo pipefail

python3 changelog.py "$@" 2>/dev/null || python changelog.py "$@"
