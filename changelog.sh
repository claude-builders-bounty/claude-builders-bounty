#!/usr/bin/env bash
# Repo-root entrypoint for bounty #1 acceptance criteria: `bash changelog.sh`
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/skills/generate-changelog/changelog.sh" "$@"
