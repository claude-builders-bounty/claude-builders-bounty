#!/usr/bin/env bash
# Ensure upstream/main merge-base exists for branch-diff attribution scans.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

cd "$REPO_ROOT"

if ! git rev-parse --verify upstream/main >/dev/null 2>&1; then
  git fetch --depth=100 https://github.com/claude-builders-bounty/claude-builders-bounty.git \
    main:refs/remotes/upstream/main 2>/dev/null || true
fi
if ! git merge-base upstream/main HEAD >/dev/null 2>&1; then
  git fetch --deepen=500 origin 2>/dev/null || \
    git fetch --deepen=500 https://github.com/claude-builders-bounty/claude-builders-bounty.git \
      main:refs/remotes/upstream/main 2>/dev/null || true
fi
