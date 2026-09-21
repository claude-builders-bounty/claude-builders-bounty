#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PARSER="$ROOT/skills/block-destructive-hook/command_parser.py"
HOOK="$ROOT/skills/block-destructive-hook/block-destructive.sh"

blocked() { python3 "$PARSER" "$1" >/dev/null 2>&1; }
allowed() { ! blocked "$1"; }

# Acceptance-critical execution paths.
blocked 'echo "$(rm -rf /)"'
blocked 'echo `rm -rf /`'
blocked "sh -c 'rm -rf /'"
blocked "bash -c 'git push --force origin main'"
blocked "eval 'rm -rf /'"
blocked 'echo $(sh -c '\''rm -rf /'\'')'

# Literal documentation remains neutral, including nested-looking examples.
allowed 'echo '\''$(rm -rf /)'\'''
allowed 'printf "%s" "git push --force"'
allowed "echo 'sh -c rm -rf /'"
allowed "echo 'eval rm -rf /'"
allowed 'echo "$(printf "%s" documentation)"'

# Existing direct rules and the actual JSON protocol.
blocked 'rm -rf /'
blocked 'rm -rf build'
blocked 'git -C repo push --force-with-lease'
blocked 'sqlite3 db "DELETE FROM users"'

HOME_DIR="$(mktemp -d)"
trap 'rm -rf "$HOME_DIR"' EXIT
mkdir -p "$HOME_DIR/.claude/hooks"
if ! printf '%s' '{"tool_name":"Bash","tool_input":{"command":"sh -c '\''rm -rf /'\''"},"cwd":"/tmp/project"}' \
  | HOME="$HOME_DIR" bash "$HOOK" | grep -q '"permissionDecision":"deny"'; then
  echo 'protocol denial failed' >&2
  exit 1
fi
grep -q 'project: /tmp/project' "$HOME_DIR/.claude/hooks/blocked.log"

printf 'block-destructive regression tests: PASS\n'
