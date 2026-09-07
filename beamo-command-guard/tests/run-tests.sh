#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK="$ROOT/hooks/block-destructive.py"
td=$(mktemp -d)
printf "%s" "{\"session_id\":\"t\",\"cwd\":\"/tmp/demo\",\"hook_event_name\":\"PreToolUse\",\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"ls -la\"}}" | HOME="$td" python3 "$HOOK"
echo smoke-allow-ok
