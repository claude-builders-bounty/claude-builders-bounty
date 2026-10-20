#!/usr/bin/env bash
set -euo pipefail
payload="$(cat)"
command="$(PAYLOAD="$payload" python3 - <<'PY'
import json, os
try:
    value = json.loads(os.environ["PAYLOAD"])
    tool_input = value.get("tool_input") or {}
    print(tool_input.get("command", ""), end="")
except (json.JSONDecodeError, TypeError, AttributeError):
    print("", end="")
PY
)"
if [[ -z "$command" ]]; then exit 0; fi
reason=""
if [[ "$command" =~ (^|[[:space:];|&])rm[[:space:]]+(-[[:alnum:]]*[rf][[:alnum:]]*|--recursive)([[:space:]]|$) ]]; then reason="recursive force deletion"
elif [[ "$command" =~ git[[:space:]]+reset[[:space:]]+--hard ]]; then reason="hard git reset"
elif [[ "$command" =~ git[[:space:]]+checkout[[:space:]]+-- ]]; then reason="discarding git changes"
elif [[ "$command" =~ chmod[[:space:]]+(-R[[:space:]]+)?777 ]]; then reason="world-writable permission change"
elif [[ "$command" =~ ^[[:space:]]*(DROP[[:space:]]+(DATABASE|TABLE|SCHEMA)|TRUNCATE([[:space:]]+TABLE)?)([[:space:]]|$) ]]; then reason="destructive SQL schema command"
elif [[ "$command" =~ ^[[:space:]]*DELETE[[:space:]]+FROM[[:space:]]+[^[:space:]]+[[:space:]]*$ ]]; then reason="DELETE without a WHERE clause"
fi
if [[ -n "$reason" ]]; then
  log_file="\${CLAUDE_HOOK_LOG:-$HOME/.claude/hooks/blocked.log}"
  mkdir -p "$(dirname "$log_file")"
  printf '%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$reason" "$command" >> "$log_file"
  printf 'Blocked potentially destructive command (%s): %s\n' "$reason" "$command" >&2
  exit 2
fi
exit 0
