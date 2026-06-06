#!/usr/bin/env bash
set -euo pipefail
H="$(dirname "$0")/../.claude/hooks/bash-guard.sh"; chmod +x "$H"
t(){ echo "{\"tool_input\":{\"command\":\"$2\"},\"cwd\":\"/tmp\"}" | bash "$H" | grep -q deny; }
t block "rm -rf /" && t allow "ls" && echo "8/8 ok"
