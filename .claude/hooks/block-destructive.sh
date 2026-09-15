#!/usr/bin/env bash
# Claude Code pre-tool-use hook: block destructive bash commands.
# Install: see README.md (2 commands).
set -euo pipefail

INPUT="$(cat || true)"
LOG_FILE="${HOME}/.claude/hooks/blocked.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Parse tool input (Claude Code hooks typically pass JSON on stdin).
TOOL_NAME=""
COMMAND=""
PROJECT_PATH="$(pwd)"
if command -v python3 >/dev/null 2>&1; then
  PARSED="$(python3 - "$INPUT" <<'PY' || true
import json, sys
raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    data = json.loads(raw) if raw.strip().startswith("{") else {}
except Exception:
    data = {}
tool = data.get("tool_name") or data.get("tool") or data.get("name") or ""
cmd = ""
tin = data.get("tool_input") or data.get("input") or data.get("arguments") or {}
if isinstance(tin, dict):
    cmd = tin.get("command") or tin.get("cmd") or tin.get("bash") or ""
elif isinstance(tin, str):
    cmd = tin
if not cmd and isinstance(data.get("command"), str):
    cmd = data["command"]
cwd = data.get("cwd") or data.get("project_path") or data.get("pwd") or ""
print(tool)
print(cmd)
print(cwd)
PY
)"
  TOOL_NAME="$(printf '%s\n' "$PARSED" | sed -n '1p')"
  COMMAND="$(printf '%s\n' "$PARSED" | sed -n '2p')"
  CWD_FROM_JSON="$(printf '%s\n' "$PARSED" | sed -n '3p')"
  if [[ -n "${CWD_FROM_JSON:-}" ]]; then
    PROJECT_PATH="$CWD_FROM_JSON"
  fi
else
  COMMAND="$INPUT"
fi

# Only gate Bash/shell tool calls; never block other tools.
case "${TOOL_NAME,,}" in
  ""|bash|shell|Bash|Shell|*bash*|*shell*)
    ;;
  *)
    exit 0
    ;;
esac

# If no command parsed, allow (do not interfere with normal / unknown payloads).
if [[ -z "${COMMAND// }" ]]; then
  exit 0
fi

# Normalize for matching (collapse whitespace).
NORM="$(printf '%s' "$COMMAND" | tr '\n' ' ' | sed -E 's/[[:space:]]+/ /g')"

blocked_reason=""

# rm -rf (and common variants)
if printf '%s' "$NORM" | grep -Eiq '(^|[[:space:];|&])rm[[:space:]]+(-[a-zA-Z]*r[a-zA-Z]*f|-rf|-fr)([[:space:]]|$)'; then
  blocked_reason="Blocked: destructive recursive delete (rm -rf)."
fi

# git push --force / -f
if [[ -z "$blocked_reason" ]] && printf '%s' "$NORM" | grep -Eiq 'git[[:space:]]+push.*(^|[[:space:]])(--force|-f)([[:space:]]|$)'; then
  blocked_reason="Blocked: force-push to remote (git push --force)."
fi

# DROP TABLE
if [[ -z "$blocked_reason" ]] && printf '%s' "$NORM" | grep -Eiq 'drop[[:space:]]+table'; then
  blocked_reason="Blocked: DROP TABLE would destroy data."
fi

# TRUNCATE
if [[ -z "$blocked_reason" ]] && printf '%s' "$NORM" | grep -Eiq 'truncate([[:space:]]+table)?[[:space:]]'; then
  blocked_reason="Blocked: TRUNCATE would wipe table data."
fi

# DELETE FROM without WHERE
if [[ -z "$blocked_reason" ]] && printf '%s' "$NORM" | grep -Eiq 'delete[[:space:]]+from[[:space:]]+[^;]+'; then
  if ! printf '%s' "$NORM" | grep -Eiq 'delete[[:space:]]+from[[:space:]]+[^;]+[[:space:]]+where[[:space:]]'; then
    blocked_reason="Blocked: DELETE FROM without a WHERE clause."
  fi
fi

if [[ -n "$blocked_reason" ]]; then
  ts="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  printf '%s | project=%s | command=%s\n' "$ts" "$PROJECT_PATH" "$COMMAND" >> "$LOG_FILE"
  # Claude Code: non-zero exit + stderr message blocks the tool and shows why.
  printf '%s\nLogged to %s\n' "$blocked_reason" "$LOG_FILE" >&2
  exit 2
fi

exit 0
