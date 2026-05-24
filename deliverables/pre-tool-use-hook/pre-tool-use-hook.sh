#!/usr/bin/env bash
# =============================================================================
# pre-tool-use-hook.sh — Claude Code Pre-Tool-Use Hook
# Intercepts and blocks dangerous bash commands before execution
# =============================================================================
# Installation:
#   mkdir -p ~/.claude/hooks
#   cp pre-tool-use-hook.sh ~/.claude/hooks/pre-tool-use-hook.sh
#   chmod +x ~/.claude/hooks/pre-tool-use-hook.sh
# =============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# ── Dangerous patterns (regex) ───────────────────────────────────────────────
# Each pattern is a regex that matches the full command line
DANGEROUS_PATTERNS=(
  # Destructive file operations
  'rm\s+-rf'
  'rm\s+-fr'
  'rmdir\s+-f'
  'mv.*/dev/null'
  '>.*&&\s*rm'

  # Database destruction
  'DROP\s+TABLE'
  'DROP\s+DATABASE'
  'TRUNCATE\s+TABLE'
  'TRUNCATE\s+'
  'DELETE\s+FROM\s+[a-zA-Z_][a-zA-Z0-9_]*\s*$'           # DELETE FROM table (no WHERE)
  'DELETE\s+FROM\s+[a-zA-Z_][a-zA-Z0-9_]*\s+WHERE\s+1\s*=\s*0'  # DELETE FROM table WHERE 1=0
  'DELETE\s+FROM\s+[a-zA-Z_][a-zA-Z0-9_]*\s+WHERE\s+TRUE'       # DELETE FROM table WHERE TRUE

  # Git destruction
  'git\s+push\s+--force'
  'git\s+push\s+-f'
  'git\s+reset\s+--hard'
  'git\s+clean\s+-fdx'
  'git\s+clean\s+-dfx'

  # Shell destruction
  'exec\s+>.*/'
  'exec\s+>&-'
  'exec\s+<.*/'
  ':>\s*'  # Truncate file: > file or : > file

  # System destruction
  'mkfs'
  'dd\s+if=.*of=/dev/'
  'fdisk'
  'parted'
  'shutdown'
  'reboot'
  'poweroff'
  'rmmod'
  'insmod'
  'modprobe'

  # Package destruction
  'apt-get\s+remove'
  'apt-get\s+purge'
  'apt-get\s+autoremove'
  'yum\s+remove'
  'dnf\s+remove'
  'brew\s+uninstall'
  'pip\s+uninstall'
  'npm\s+uninstall'
)

# ── Get the command to check ─────────────────────────────────────────────────
# Claude Code passes the command via stdin or as arguments
# The hook receives the tool name and arguments
if [[ $# -lt 1 ]]; then
  # No arguments — read from stdin
  read -r -t 5 COMMAND_LINE || exit 0
else
  # Reconstruct command from arguments
  COMMAND_LINE="$*"
fi

# Skip if empty
if [[ -z "$COMMAND_LINE" ]]; then
  exit 0
fi

# ── Check against dangerous patterns ─────────────────────────────────────────
BLOCKED=false
MATCHED_PATTERN=""

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND_LINE" | grep -qiE "$pattern"; then
    BLOCKED=true
    MATCHED_PATTERN="$pattern"
    break
  fi
done

# ── If blocked, log and exit with error ──────────────────────────────────────
if [[ "$BLOCKED" == true ]]; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  PROJECT_PATH="$(pwd)"

  # Log the blocked attempt
  echo "[${TIMESTAMP}] BLOCKED | Pattern: ${MATCHED_PATTERN} | Command: ${COMMAND_LINE} | Path: ${PROJECT_PATH}" >> "$LOG_FILE"

  # Output error message for Claude
  cat << EOF
🚫 **Command Blocked by Pre-Tool-Use Hook**

The following command was blocked because it matches a dangerous pattern:

\`\`\`
${COMMAND_LINE}
\`\`\`

**Matched pattern:** \`${MATCHED_PATTERN}\`

This command could cause irreversible damage:
- Data loss (rm -rf, DROP TABLE, TRUNCATE)
- Force push to remote (git push --force)
- System destruction (mkfs, dd to /dev/)
- Package removal (apt remove, pip uninstall)

**What to do:**
1. Review the command carefully
2. If you meant to run it, use the \`--force\` flag to bypass the hook
3. Consider safer alternatives (e.g., \`rm -i\` for interactive deletion)

EOF

  exit 1
fi

# ── Command is safe — allow execution ────────────────────────────────────────
exit 0
