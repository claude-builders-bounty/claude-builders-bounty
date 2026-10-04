#!/usr/bin/env bash
# Forward the Bash entry point to the existing changelog generator.
set -euo pipefail

CHANGELOG_SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

# Preserve the original no-argument and single-output-path invocations.
# Explicit Python options, including --repo outside a worktree, pass through.
if (($# == 0)); then
  if ! CHANGELOG_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
    printf 'changelog.sh: run this command inside a Git repository or pass --repo PATH\n' >&2
    exit 2
  fi
  set -- --repo "$CHANGELOG_REPO_ROOT"
elif (($# == 1)) && [[ $1 != -* ]]; then
  CHANGELOG_OUTPUT=$1
  if [[ $CHANGELOG_OUTPUT != /* ]]; then
    CHANGELOG_OUTPUT=$PWD/$CHANGELOG_OUTPUT
  fi
  if ! CHANGELOG_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
    printf 'changelog.sh: run this command inside a Git repository or pass --repo PATH\n' >&2
    exit 2
  fi
  set -- --repo "$CHANGELOG_REPO_ROOT" --output "$CHANGELOG_OUTPUT"
fi

exec python3 "$CHANGELOG_SCRIPT_DIR/changelog.py" "$@"
