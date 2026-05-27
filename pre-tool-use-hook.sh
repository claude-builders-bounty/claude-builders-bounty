#!/usr/bin/env bash
# pre-tool-use-hook.sh - Blocks destructive bash commands
set -euo pipefail
CMD="$*"
for p in "rm -rf /" "rm -rf ~" "dd if=" "mkfs" "git push --force" "drop database" "wallet send"; do
  if echo "$CMD" | grep -qiE "$p" 2>/dev/null; then
    echo "BLOCKED: $p"
    exit 1
  fi
done
exit 0
