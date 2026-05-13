#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT}" ]]; then
  echo "error: not inside a git repository" >&2
  exit 2
fi

SCRIPT="${ROOT}/.claude/skills/generate-changelog/scripts/generate_changelog.py"
if [[ ! -f "${SCRIPT}" ]]; then
  echo "error: missing script at ${SCRIPT}" >&2
  echo "hint: copy .claude/skills/generate-changelog into this repo first" >&2
  exit 2
fi

python3 "${SCRIPT}" "$@"

