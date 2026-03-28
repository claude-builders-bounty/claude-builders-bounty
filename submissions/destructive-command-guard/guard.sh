#!/usr/bin/env bash
# guard.sh — Claude Code pre-tool-use hook
# Blocks destructive bash commands before execution.
#
# Exit codes (Claude Code hook protocol):
#   0 = allow the command
#   2 = block the command (hook rejects it)
#
# Reads JSON from stdin: { "tool_name": "Bash", "tool_input": { "command": "..." } }

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LOG_FILE="${CLAUDE_HOOKS_DIR:-$HOME/.claude/hooks}/blocked.log"
PROJECT_DIR="${PWD}"

# ---------------------------------------------------------------------------
# Read tool invocation from stdin
# ---------------------------------------------------------------------------
INPUT="$(cat)"

# Extract tool name — only intercept Bash tool calls
TOOL_NAME="$(printf '%s' "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')"

if [[ "$TOOL_NAME" != "Bash" ]]; then
    exit 0
fi

# Extract the command string from tool_input.command
# Use python3 if available for robust JSON parsing, fall back to grep/sed
if command -v python3 &>/dev/null; then
    COMMAND="$(printf '%s' "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null)" || COMMAND=""
fi

# Fallback: regex extraction if python3 failed or is unavailable
if [[ -z "${COMMAND:-}" ]]; then
    COMMAND="$(printf '%s' "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')"
fi

# If we still have no command, allow (nothing to check)
if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# ---------------------------------------------------------------------------
# Normalize: collapse whitespace for pattern matching
# ---------------------------------------------------------------------------
NORMALIZED="$(printf '%s' "$COMMAND" | tr -s '[:space:]' ' ')"

# ---------------------------------------------------------------------------
# Helper: block a command, log it, print reason, exit 2
# ---------------------------------------------------------------------------
block() {
    local reason="$1"
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"

    # Append to log file
    printf '%s | BLOCKED | %s | project=%s | command=%s\n' \
        "$timestamp" "$reason" "$PROJECT_DIR" "$COMMAND" >> "$LOG_FILE"

    # Print human-readable message for Claude
    cat <<EOF
BLOCKED: $reason

The following command was prevented from executing:
  $COMMAND

This hook blocks destructive commands to protect your system and data.
The attempt has been logged to $LOG_FILE.
If this is intentional, temporarily disable the hook in your Claude Code settings.
EOF

    exit 2
}

# ---------------------------------------------------------------------------
# Pattern checks (case-insensitive via shell options)
# ---------------------------------------------------------------------------

# --- rm -rf dangerous paths ---
# Block: rm -rf /, rm -rf ~, rm -rf .  (with optional flags mixed in)
# Allow: rm -rf node_modules/, rm -rf ./dist, rm -rf /tmp/build, etc.
if printf '%s' "$NORMALIZED" | grep -iqE '\brm\b[[:space:]]+-[a-z]*r[a-z]*f[^[:alnum:]]|rm\b[[:space:]]+-[a-z]*f[a-z]*r[^[:alnum:]]'; then
    # Extract the target path(s) after rm and its flags
    # Check for dangerous root/home/cwd targets
    if printf '%s' "$NORMALIZED" | grep -iqE '\brm\b[[:space:]]+-[a-z]*rf[[:space:]]+(/[[:space:]]|/\*|~[[:space:]]|~\/[[:space:]]|\.[[:space:]]|\.\*|/\"|/'"'"')'; then
        block "rm -rf targeting root (/), home (~), or current directory (.) is extremely dangerous"
    fi
    if printf '%s' "$NORMALIZED" | grep -iqE '\brm\b[[:space:]]+-[a-z]*fr[[:space:]]+(/[[:space:]]|/\*|~[[:space:]]|~\/[[:space:]]|\.[[:space:]]|\.\*|/\"|/'"'"')'; then
        block "rm -rf targeting root (/), home (~), or current directory (.) is extremely dangerous"
    fi
    # Also catch: rm -rf / at end of line (no trailing space)
    if printf '%s' "$NORMALIZED" | grep -iqE '\brm\b[[:space:]]+-[a-z]*r[a-z]*f[[:space:]]+(/|~|\.)$'; then
        block "rm -rf targeting root (/), home (~), or current directory (.) is extremely dangerous"
    fi
fi

# --- DROP TABLE ---
if printf '%s' "$NORMALIZED" | grep -iqE '\bDROP[[:space:]]+TABLE\b'; then
    block "DROP TABLE detected — this would permanently destroy database tables"
fi

# --- TRUNCATE ---
if printf '%s' "$NORMALIZED" | grep -iqE '\bTRUNCATE\b'; then
    block "TRUNCATE detected — this would delete all rows from a table"
fi

# --- DELETE FROM without WHERE ---
if printf '%s' "$NORMALIZED" | grep -iqE '\bDELETE[[:space:]]+FROM\b'; then
    if ! printf '%s' "$NORMALIZED" | grep -iqE '\bDELETE[[:space:]]+FROM\b.*\bWHERE\b'; then
        block "DELETE FROM without a WHERE clause — this would delete all rows from a table"
    fi
fi

# --- git push --force to main/master ---
# Catches: git push --force, git push -f, git push --force-with-lease
# Only blocks when targeting main or master (or no branch specified, which defaults to current)
if printf '%s' "$NORMALIZED" | grep -iqE '\bgit[[:space:]]+push\b.*(\s--force\b|\s--force-with-lease\b|\s-f\b)'; then
    # Check if explicitly targeting a non-main/master branch
    # If targeting main/master or no explicit branch, block
    if printf '%s' "$NORMALIZED" | grep -iqE '\bgit[[:space:]]+push\b.*\b(main|master)\b'; then
        block "git push --force to main/master — force-pushing to protected branches can destroy shared history"
    fi
    # If no remote branch specified at all (bare force push), also block
    if printf '%s' "$NORMALIZED" | grep -iqE '\bgit[[:space:]]+push[[:space:]]+--force[[:space:]]*$|\bgit[[:space:]]+push[[:space:]]+-f[[:space:]]*$'; then
        block "git push --force with no explicit branch — could force-push to main/master"
    fi
fi

# ---------------------------------------------------------------------------
# All checks passed — allow the command
# ---------------------------------------------------------------------------
exit 0
