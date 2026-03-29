#!/usr/bin/env bash
# guard.sh — Claude Code PreToolUse hook that blocks destructive bash commands
# Pure bash + jq. No external dependencies beyond jq (ships with most systems).
#
# Exit behavior (per Claude Code hooks spec):
#   exit 0 + JSON stdout with permissionDecision:"deny"  => block the command
#   exit 0 + empty stdout                                 => allow the command
#   exit 2 + stderr message                               => block (legacy style)
#
# Usage:
#   As a hook:  Claude Code pipes JSON on stdin automatically
#   Standalone: echo '{"tool_input":{"command":"rm -rf /"}}' | ./guard.sh
#   Dry-run:    echo '{"tool_input":{"command":"rm -rf /"}}' | ./guard.sh --dry-run

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BLOCKED_LOG="${CLAUDE_GUARD_LOG:-$HOME/.claude/hooks/blocked.log}"
CUSTOM_PATTERNS_FILE="${CLAUDE_GUARD_PATTERNS:-$HOME/.claude/hooks/guard-patterns.txt}"
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
  esac
done

# ---------------------------------------------------------------------------
# Read stdin (Claude Code sends JSON)
# ---------------------------------------------------------------------------
INPUT=$(cat)

# If stdin is empty, nothing to check
if [[ -z "$INPUT" ]]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# Extract fields
# ---------------------------------------------------------------------------
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
PROJECT_DIR=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)

# Only inspect Bash tool calls — let everything else through
if [[ "$TOOL_NAME" != "Bash" && -n "$TOOL_NAME" ]]; then
  exit 0
fi

# No command to inspect
if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# Normalize command for matching
# ---------------------------------------------------------------------------
# Collapse whitespace, lowercase for case-insensitive SQL matching
NORMALIZED=$(echo "$COMMAND" | tr '\n' ' ' | sed 's/  */ /g')
NORMALIZED_UPPER=$(echo "$NORMALIZED" | tr '[:lower:]' '[:upper:]')

# ---------------------------------------------------------------------------
# Built-in dangerous patterns
# ---------------------------------------------------------------------------
block_reason=""

# 1. rm -rf (always dangerous — recursive force delete)
#    Matches: rm -rf, rm -fr, rm -r -f, rm -f -r, sudo rm -rf, xargs rm -rf
if echo "$NORMALIZED" | grep -qE '\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b'; then
  block_reason="rm -rf detected — recursive force deletion is blocked"
elif echo "$NORMALIZED" | grep -qP '\brm\s+(?=.*-[a-zA-Z]*r)(?=.*-[a-zA-Z]*f)'; then
  block_reason="rm -rf detected — recursive force deletion is blocked"
fi

# 2. DROP TABLE
if [[ -z "$block_reason" ]] && echo "$NORMALIZED_UPPER" | grep -qE '\bDROP\s+TABLE\b'; then
  block_reason="DROP TABLE detected — dropping database tables is blocked"
fi

# 3. git push --force (including -f shorthand)
if [[ -z "$block_reason" ]] && echo "$NORMALIZED" | grep -qE '\bgit\s+push\s+.*(-f|--force(-with-lease)?)\b'; then
  block_reason="git push --force detected — force pushing is blocked"
fi

# 4. TRUNCATE
if [[ -z "$block_reason" ]] && echo "$NORMALIZED_UPPER" | grep -qE '\bTRUNCATE\b'; then
  block_reason="TRUNCATE detected — truncating tables is blocked"
fi

# 5. DELETE FROM without WHERE
if [[ -z "$block_reason" ]]; then
  if echo "$NORMALIZED_UPPER" | grep -qE '\bDELETE\s+FROM\b'; then
    if ! echo "$NORMALIZED_UPPER" | grep -qE '\bDELETE\s+FROM\b.*\bWHERE\b'; then
      block_reason="DELETE FROM without WHERE clause — unfiltered deletion is blocked"
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Custom patterns (one regex per line in guard-patterns.txt)
# ---------------------------------------------------------------------------
if [[ -z "$block_reason" && -f "$CUSTOM_PATTERNS_FILE" ]]; then
  while IFS= read -r pattern || [[ -n "$pattern" ]]; do
    # Skip empty lines and comments
    [[ -z "$pattern" || "$pattern" =~ ^# ]] && continue
    if echo "$NORMALIZED" | grep -qE "$pattern"; then
      block_reason="Custom pattern matched: $pattern"
      break
    fi
  done < "$CUSTOM_PATTERNS_FILE"
fi

# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------
if [[ -n "$block_reason" ]]; then
  TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

  # Log blocked attempt
  if [[ "$DRY_RUN" = false ]]; then
    mkdir -p "$(dirname "$BLOCKED_LOG")"
    printf '%s | BLOCKED | project=%s | reason=%s | command=%s\n' \
      "$TIMESTAMP" \
      "${PROJECT_DIR:-unknown}" \
      "$block_reason" \
      "$COMMAND" \
      >> "$BLOCKED_LOG"
  fi

  # Dry-run mode: print to stderr and exit without blocking
  if [[ "$DRY_RUN" = true ]]; then
    echo "[DRY-RUN] WOULD BLOCK: $block_reason" >&2
    echo "[DRY-RUN] Command: $COMMAND" >&2
    exit 0
  fi

  # Output JSON to block the command (exit 0 + deny decision)
  jq -n \
    --arg reason "$block_reason" \
    '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: ("BLOCKED by guard hook: " + $reason + ". Use a safer alternative or ask the user for confirmation before retrying.")
      }
    }'
  exit 0
fi

# Command is safe — allow it (exit 0, no output)
exit 0
