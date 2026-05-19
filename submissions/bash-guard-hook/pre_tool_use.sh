#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# Pre-tool-use hook — Block destructive bash commands
# Place at: ~/.claude/hooks/pre_tool_use.sh
# Make executable: chmod +x ~/.claude/hooks/pre_tool_use.sh
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Read input from Claude Code (JSON on stdin) ────────────────────
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# ── Only check bash/terminal commands ──────────────────────────────
if [[ "$TOOL_NAME" != "bash" && "$TOOL_NAME" != "terminal" && "$TOOL_NAME" != "shell" ]]; then
  echo '{"allow": true, "reason": "not a shell command"}'
  exit 0
fi

if [[ -z "$COMMAND" ]]; then
  echo '{"allow": true, "reason": "no command"}'
  exit 0
fi

# ── Whitelist: known-safe patterns ─────────────────────────────────
if echo "$COMMAND" | grep -qE 'rm -rf (node_modules|\.next|dist|build|__pycache__|tmp/)'; then
  echo '{"allow": true, "reason": "safe cleanup pattern"}'
  exit 0
fi

# ── DESTRUCTIVE PATTERNS ───────────────────────────────────────────
BLOCKED=""
SEVERITY=""

check() {
  local pattern="$1"
  local name="$2"
  local sev="$3"
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    BLOCKED="$BLOCKED$name, "
    [[ "$sev" == "critical" ]] && SEVERITY="critical"
    [[ "$sev" == "high" && "$SEVERITY" != "critical" ]] && SEVERITY="high"
    [[ "$sev" == "medium" && -z "$SEVERITY" ]] && SEVERITY="medium"
  fi
}

# File system
check '\brm +-[rRf]+ *(/|~|\*)'                        "rm root"        "critical"
check 'dd +if='                                         "dd disk write"  "high"
check 'mkfs\.'                                          "mkfs format"    "critical"
check '> */dev/sd[a-z]'                                "overwrite disk" "critical"
check 'chmod +(-R +)?777 +/'                            "chmod 777 /"    "high"
check ':\(\) \{ :\|:& \};:'                             "fork bomb"      "critical"

# Database
check '\bDROP +(TABLE|DATABASE)\b'                      "DROP TABLE/DB"  "critical"
check '\bDELETE +FROM +\S+ *$'                          "DELETE no WHERE" "high"

# Git
check '\bgit +push +(-f|--force)\b'                     "force push"     "high"
check '\bgit +reset +--hard\b'                          "git reset hard" "medium"

# System
check '\bcurl.*\| *(ba)?sh\b'                           "curl pipe bash" "medium"
check '\bwget.*\| *(ba)?sh\b'                           "wget pipe bash" "medium"
check '> *~?/\.(bashrc|zshrc|profile|env)'              "overwrite rc"   "high"
check '\b(shutdown|reboot|halt)\b'                      "shutdown"       "high"

# Docker
check '\bdocker +(system +)?prune\b'                    "docker prune"   "medium"
check '\bdocker +compose +down +-v\b'                   "compose down -v" "medium"

# ── Result ─────────────────────────────────────────────────────────
if [[ -n "$BLOCKED" ]]; then
  BLOCKED="${BLOCKED%, }"  # Remove trailing comma+space
  SEVERITY="${SEVERITY:-medium}"
  echo "{\"allow\": false, \"reason\": \"🚫 BLOCKED: $BLOCKED\", \"severity\": \"$SEVERITY\"}"
  exit 0
fi

echo '{"allow": true, "reason": "OK"}'
