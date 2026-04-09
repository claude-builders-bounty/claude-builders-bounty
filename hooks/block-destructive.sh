#!/usr/bin/env bash
# Pre-tool-use hook: blocks destructive bash commands
BLOCK_PATTERNS=('^rm\s+(-rf?|--recursive|--force)\s+(/|~|\$HOME)' '^dd\s+.*of=/dev/' '^mkfs' '^chmod\s+-R\s+777' '^:\(\)\{.*\}.*;' 'wget.*\|\s*(ba)?sh' 'curl.*\|\s*(ba)?sh' '^drop\s+database' '^git\s+push\s+--force')
ALLOW_PATTERNS=('^rm\s+-rf\s+/\./' '^rm\s+-rf\s+\./node_modules' '^rm\s+-rf\s+\./dist' '^rm\s+-rf\s+\./build' '^rm\s+-rf\s+/tmp/')
check_command() {
  local cmd="$1"
  for pattern in "${ALLOW_PATTERNS[@]}"; do echo "$cmd" | grep -qiE "$pattern" && return 0; done
  for pattern in "${BLOCK_PATTERNS[@]}"; do echo "$cmd" | grep -qiE "$pattern" && return 1; done
  return 0
}
[ $# -gt 0 ] && check_command "$*" && exit $?
