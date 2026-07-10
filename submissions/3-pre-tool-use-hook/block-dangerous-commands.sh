#!/usr/bin/env bash
# =============================================================================
# Claude Code Pre-Tool-Use Hook — Block Destructive Commands
# Bounty: #3 - $100
# =============================================================================
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
LOG_FILE="${HOME}/.claude/hooks/blocked.log"
ALLOW_FILE="$(dirname "$0")/.dangerous-allowlist"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# ── Dangerous Patterns ──────────────────────────────────────────────────────
# Each entry: PATTERN|SEVERITY|REASON
DANGEROUS_PATTERNS=$(cat <<'EOF'
rm -rf[[:space:]]+/|CRITICAL|Recursive force delete of root filesystem
rm[[:space:]]+-rf[[:space:]]+/|CRITICAL|Recursive force delete of root filesystem
DROP[[:space:]]+TABLE|CRITICAL|Destructive database operation
DROP[[:space:]]+DATABASE|CRITICAL|Destructive database operation
TRUNCATE[[:space:]]+TABLE|HIGH|Table truncation — data loss
DELETE[[:space:]]+FROM(?!.*WHERE)|HIGH|Unconditional DELETE without WHERE clause
UPDATE[[:space:]]+.*SET(?!.*WHERE)|HIGH|Unconditional UPDATE without WHERE clause
git[[:space:]]+push[[:space:]]+--force|CRITICAL|Force push — overwrites remote history
git[[:space:]]+push[[:space:]]+-f[[:space:]]|CRITICAL|Force push — overwrites remote history
git[[:space:]]+push[[:space:]]+origin[[:space:]]+.*:[[:space:]]*--force|CRITICAL|Force push to origin
git[[:space:]]+reset[[:space:]]+--hard|HIGH|Hard reset — discards uncommitted changes
git[[:space:]]+branch[[:space:]]+-D|HIGH|Force delete branch
chmod[[:space:]]+777|HIGH|Overly permissive file permissions
chown[[:space:]]+-R|MEDIUM|Recursive ownership change
dd[[:space:]]+if=|CRITICAL|Direct disk write
mkfs\.|CRITICAL|Filesystem creation — data destruction
fdisk|CRITICAL|Partition manipulation
:wq!|MEDIUM|Vim force write — potential config change
EOF
)

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
ORANGE='\033[0;33m'
NC='\033[0m' # No Color

# ── Logging ──────────────────────────────────────────────────────────────────
log_block() {
  local cmd="$1"
  local severity="$2"
  local reason="$3"
  local timestamp
  timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  local hostname="${HOSTNAME:-unknown}"
  echo "[${timestamp}] [${severity}] [${hostname}] [${USER}] Blocked: ${cmd} — ${reason}" >> "$LOG_FILE"
  # Keep log manageable — last 1000 lines
  tail -n 1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
}

# ── Allowlist Check ──────────────────────────────────────────────────────────
is_allowed() {
  local cmd="$1"
  if [[ -f "$ALLOW_FILE" ]]; then
    while IFS= read -r pattern; do
      [[ -z "$pattern" ]] && continue
      if echo "$cmd" | grep -qiE "$pattern"; then
        return 0
      fi
    done < "$ALLOW_FILE"
  fi
  return 1
}

# ── Input ────────────────────────────────────────────────────────────────────
TOOL_NAME="${CLAUDE_TOOL_NAME:-${1:-}}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-${2:-}}"

# If no input from env vars, read from stdin
if [[ -z "$TOOL_NAME" ]] && [[ -z "$TOOL_INPUT" ]]; then
  read -r TOOL_INPUT
fi

# ── Scan ─────────────────────────────────────────────────────────────────────
BLOCKED=0

while IFS='|' read -r pattern severity reason; do
  [[ -z "$pattern" ]] && continue

  if echo "$TOOL_INPUT" | grep -qiE "$pattern" 2>/dev/null; then
    # Check allowlist
    if is_allowed "$TOOL_INPUT"; then
      echo -e "${ORANGE}⚠️  Allowed (in allowlist):${NC} ${TOOL_INPUT:0:120}"
      continue
    fi

    BLOCKED=1
    log_block "$TOOL_INPUT" "$severity" "$reason"

    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  🛑  BLOCKED: Dangerous Command Detected${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${YELLOW}Severity:${NC} ${severity}"
    echo -e "  ${YELLOW}Reason:${NC}   ${reason}"
    echo -e "  ${YELLOW}Command:${NC}  ${TOOL_INPUT:0:200}"
    echo ""
    echo -e "  ${ORANGE}To allow this pattern, add it to:${NC}"
    echo -e "  ${ALLOW_FILE}"
    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    exit 1
  fi
done <<< "$DANGEROUS_PATTERNS"

# If we get here, command is safe
exit 0
