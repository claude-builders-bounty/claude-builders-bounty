#!/usr/bin/env bash
# Pre-tool-use hook: Dangerous Command Guard (bash edition)
#
# Reads JSON from stdin, checks Bash tool commands against a blocklist,
# and outputs {"decision":"block","reason":"..."} to block, or exits 0 to allow.
#
# Env vars:
#   ALLOW_DANGEROUS=1   — override block (still audit-logs)
#   HOOK_DRY_RUN=1      — explain without blocking
#   CLAUDE_PROJECT_DIR  — project path (set by Claude Code)

set -euo pipefail

# ── Paths ────────────────────────────────────────────────────────────────────
HOOKS_DIR="${HOME}/.claude/hooks"
BLOCKED_LOG="${HOOKS_DIR}/blocked.log"

# ── Colour helpers ────────────────────────────────────────────────────────────
if [[ -t 2 ]]; then
  RED=$'\033[1;31m'; YELLOW=$'\033[1;33m'; CYAN=$'\033[1;36m'
  BOLD=$'\033[1m';   RESET=$'\033[0m'
else
  RED=''; YELLOW=''; CYAN=''; BOLD=''; RESET=''
fi

# ── Read stdin ────────────────────────────────────────────────────────────────
INPUT="$(cat)"

# Extract tool_name (jq preferred, fallback to python3)
if command -v jq &>/dev/null; then
  TOOL_NAME="$(printf '%s' "$INPUT" | jq -r '.tool_name // ""')"
  COMMAND="$(printf '%s' "$INPUT"   | jq -r '.tool_input.command // ""')"
else
  TOOL_NAME="$(printf '%s' "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))")"
  COMMAND="$(printf '%s' "$INPUT"   | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))")"
fi

[[ "$TOOL_NAME" != "Bash" ]] && exit 0
[[ -z "$COMMAND" ]]          && exit 0

PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# ── Pattern matching ──────────────────────────────────────────────────────────
MATCHED_REASON=""
SEVERITY=""

check() {
  local regex="$1" reason="$2" sev="$3"
  if echo "$COMMAND" | grep -Eiq "$regex"; then
    MATCHED_REASON="$reason"
    SEVERITY="$sev"
    return 0
  fi
  return 1
}

# Filesystem
check 'rm\s+.*-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*'       "rm recursive+force (rm -rf)"              "CRITICAL" ||
check 'rm\s+.*-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*'        "rm force+recursive (rm -fr)"              "CRITICAL" ||
check 'find\s+.*--delete'                              "find … --delete (mass deletion)"          "HIGH"     ||
check 'find\s+.*-delete'                               "find … -delete (mass deletion)"           "HIGH"     ||
check 'dd\s+.*if\s*=\s*/dev/(zero|null|random)'       "dd from /dev/zero|null (disk wipe)"       "CRITICAL" ||
check '\b(mkfs|mke2fs|mkntfs|mkswap)\b'               "filesystem format command"                "CRITICAL" ||
check '\bshred\s+'                                     "shred (secure file deletion)"             "HIGH"     ||
check '>\s*/dev/(sda|sdb|sdc|hda|nvme[0-9])'         "write to raw block device"                "CRITICAL" ||
# SQL
check '\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW)\b' "SQL DROP TABLE/DATABASE/…"                "CRITICAL" ||
check '\bTRUNCATE\s+(TABLE\s+)?\w+'                   "SQL TRUNCATE TABLE"                       "HIGH"     ||
check '\bDELETE\s+FROM\s+\w+\s*(;|$)'                "SQL DELETE FROM without WHERE"            "HIGH"     ||
check '\bDELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1'   "SQL DELETE … WHERE 1=1"                   "CRITICAL" ||
# Git
check '\bgit\s+push\s+.*(--force|-f)\b'               "git push --force (overwrites history)"    "HIGH"     ||
check '\bgit\s+reset\s+--hard\s+HEAD[~^][0-9]*'       "git reset --hard HEAD~ (discards commits)""HIGH"     ||
check '\bgit\s+clean\s+.*-[a-zA-Z]*f[a-zA-Z]*d'      "git clean -fd (removes untracked files)"  "MEDIUM"   ||
check '\bgit\s+clean\s+.*-[a-zA-Z]*d[a-zA-Z]*f'      "git clean -df (removes untracked files)"  "MEDIUM"   ||
# Kubernetes
check '\bkubectl\s+delete\s+(namespace|ns)\b'         "kubectl delete namespace"                 "CRITICAL" ||
check '\bkubectl\s+delete\s+(all|pods|deployments)\s+--all\b' "kubectl delete all --all"         "CRITICAL" ||
check '\bkubectl\s+delete\s+.*--all-namespaces\b'     "kubectl delete … --all-namespaces"        "CRITICAL" ||
# System
check '\bkill\s+(-9\s+)?-1\b'                         "kill -1 (kills all user processes)"       "CRITICAL" ||
true  # ensure the chain always succeeds

# ── No match → allow ──────────────────────────────────────────────────────────
[[ -z "$MATCHED_REASON" ]] && exit 0

# ── Dry-run mode ──────────────────────────────────────────────────────────────
log_entry() {
  local prefix="$1"
  mkdir -p "$HOOKS_DIR"
  local ts; ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  printf '[%s] %s | project=%q | reason=%q | cmd=%q\n' \
    "$ts" "$prefix" "$PROJECT" "$MATCHED_REASON" "$COMMAND" >> "$BLOCKED_LOG"
}

banner() {
  local header="$1"
  local sep; sep="$(printf '─%.0s' {1..72})"
  echo ""                                              >&2
  echo "$sep"                                          >&2
  echo "$header"                                       >&2
  echo "$sep"                                          >&2
  printf '  %sReason  :%s %s\n' "$BOLD" "$RESET" "$MATCHED_REASON" >&2
  printf '  %sCommand :%s %s\n' "$BOLD" "$RESET" "${COMMAND:0:120}">&2
  printf '  %sProject :%s %s\n' "$BOLD" "$RESET" "$PROJECT"        >&2
}

DRY_RUN="${HOOK_DRY_RUN:-0}"
ALLOW="${ALLOW_DANGEROUS:-0}"

if [[ "$DRY_RUN" == "1" || "$DRY_RUN" == "true" ]]; then
  banner "${YELLOW}[DRY-RUN] Would block — severity: ${SEVERITY}${RESET}"
  echo "" >&2
  printf '{"decision":"allow","reason":"[DRY-RUN] Would have blocked: %s"}\n' "$MATCHED_REASON"
  exit 0
fi

if [[ "$ALLOW" == "1" || "$ALLOW" == "true" ]]; then
  log_entry "OVERRIDE_ALLOWED"
  banner "${YELLOW}⚠  DANGEROUS COMMAND ALLOWED (ALLOW_DANGEROUS=1 override) — severity: ${SEVERITY}${RESET}"
  echo "" >&2
  exit 0   # allow
fi

# ── Block ─────────────────────────────────────────────────────────────────────
log_entry "BLOCKED"
banner "${RED}✗  BLOCKED — severity: ${SEVERITY}${RESET}"
cat >&2 <<EOF

  ${CYAN}To allow once:${RESET} ALLOW_DANGEROUS=1 <re-run>
  ${CYAN}Audit log    :${RESET} ${BLOCKED_LOG}

$(printf '─%.0s' {1..72})
EOF

BLOCK_MSG="BLOCKED by dangerous_command_guard: ${MATCHED_REASON}. This command was blocked because it is potentially destructive and irreversible. If you are certain this is safe, ask the user to re-run with ALLOW_DANGEROUS=1 (audit-logged)."

printf '{"decision":"block","reason":"%s"}\n' \
  "$(printf '%s' "$BLOCK_MSG" | sed 's/"/\\"/g')"

exit 0
