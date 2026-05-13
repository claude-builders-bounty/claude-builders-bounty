#!/usr/bin/env bash
set -euo pipefail
COMMAND=$(cat)
BLOCKED_CMDS=("rm -rf /" "rm -rf ~" "dd if=" "mkfs")
DANGEROUS=("rm -rf" "sudo " "git push --force" "drop table" "truncate" "curl.*| sh" "wget.*| bash")
for blocked in "${BLOCKED_CMDS[@]}"; do
    if echo "$COMMAND" | grep -qiF "$blocked"; then
        echo '{"allowed": false, "reason": "Blocked: destructive command"}'; exit 0
    fi
done
for pattern in "${DANGEROUS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        echo '{"allowed": false, "reason": "Blocked: dangerous pattern"}'; exit 0
    fi
done
echo '{"allowed": true}'
