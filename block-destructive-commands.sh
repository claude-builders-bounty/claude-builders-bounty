#!/bin/bash
# block-destructive-commands.sh
# Pre-tool-use hook for AI agents

set -euo pipefail

COMMAND="$1"
NORMALIZED=$(echo "$COMMAND" | tr -s " " | sed "s/^[[:space:]]*//")

DANGEROUS_PATTERNS=(
'rm\s+-rf\s+[/~]'
'rm\s+-rf\s+\.'
'mkfs\.'
'dd\s+if=/dev/zero'
'dd\s+if=/dev/null'
'dd\s+if=/dev/urandom'
'>?/dev/sd[a-z]'
':\(\)\{\s*:\|:&\s*\};:'
'chmod\s+-R\s+777\s+/'
'chown\s+-R\s+root:root\s+/'
'nmap\s+-O'
'hping3'
'aireplay-ng'
'cat\s+/etc/shadow'
'cat\s+/etc/passwd'
'cat\s+.*\.ssh/id_rsa'
'DROP\s+DATABASE'
'DROP\s+TABLE'
'DELETE\s+FROM\s+.*\s+WHERE\s+1\s*=\s*1'
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$NORMALIZED" | grep -qiE "$pattern"; then
        echo "{\"blocked\": true, \"reason\": \"Destructive pattern matched\", \"command\": \"$COMMAND\"}" >&2
        exit 1
    fi
done

echo "{\"blocked\": false, \"command\": \"$COMMAND\"}"
exit 0
