#!/bin/bash
# pre-tool-use hook: blocks destructive bash commands
# Claude Code hook format: ~/.claude/hooks/pre-tool-use-blocker.sh
# Installation: ln -s ~/.claude/hooks/pre-tool-use-blocker.sh ~/.claude/hooks/pre-tool-use

BLOCKED_LOG="${HOME}/.claude/hooks/blocked.log"
HOOK_DIR="${HOME}/.claude/hooks"

# Read stdin JSON
stdin=$(cat)
hook_type=$(echo "$stdin" | grep -o '"hook_type"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
tool_name=$(echo "$stdin" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
command=$(echo "$stdin" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)

# Only check bash/terminal commands
if [[ "$tool_name" != "Bash" && "$tool_name" != "Terminal" && "$tool_name" != "Write" && "$tool_name" != "Read" ]]; then
    exit 0
fi

# If no command found in tool_input (e.g. Write/Read tools), allow
if [[ -z "$command" ]]; then
    exit 0
fi

# Patterns that are always dangerous
BLOCKED_PATTERNS=(
    "rm[[:space:]]+-rf[[:space:]]"
    "rm[[:space:]]+-r[[:space:]]*/"
    "rm[[:space:]]+-f[[:space:]]/"
    "dd[[:space:]]+if=.*of=/"
    "mkfs"
    "fdisk[[:space:]]-l"
    "TRUNCATE[[:space:]]"
    "TRUNCATE[[:space:]]TABLE"
    "DROP[[:space:]]TABLE"
    "DROP[[:space:]]DATABASE"
    "git[[:space:]]push[[:space:]]--force"
    "git[[:space:]]push[[:space:]]-f"
    ":(){:|:&};"  # fork bomb
)

# Check for DELETE FROM without WHERE
if echo "$command" | grep -qiE "DELETE[[:space:]]+FROM"; then
    if ! echo "$command" | grep -qiE "DELETE[[:space:]]+FROM[[:space:]]+[a-zA-Z_0-9]+[[:space:]]+WHERE"; then
        blocked=true
        reason="DELETE FROM without WHERE clause — data loss risk"
    fi
fi

# Check all other patterns
for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$command" | grep -qiE "$pattern"; then
        blocked=true
        case "$pattern" in
            "rm[[:space:]]+-rf[[:space:]]"|"rm[[:space:]]+-r[[:space:]]*/"|"rm[[:space:]]+-f[[:space:]]/")
                reason="rm -rf — recursive force delete detected"
                ;;
            "dd[[:space:]]+if=.*of=/")
                reason="dd overwrite of disk — catastrophic data loss"
                ;;
            "mkfs")
                reason="mkfs — filesystem destruction"
                ;;
            "fdisk[[:space:]]-l")
                reason="fdisk — disk partition table modification"
                ;;
            "TRUNCATE[[:space:]]"|"TRUNCATE[[:space:]]TABLE")
                reason="TRUNCATE — entire table deletion"
                ;;
            "DROP[[:space:]]TABLE")
                reason="DROP TABLE — table deletion"
                ;;
            "DROP[[:space:]]DATABASE")
                reason="DROP DATABASE — entire database deletion"
                ;;
            "git[[:space:]]push[[:space:]]--force"|"git[[:space:]]push[[:space:]]-f")
                reason="git push --force — can overwrite shared history"
                ;;
            ":(){:|:&};")
                reason="fork bomb — system resource exhaustion"
                ;;
            *)
                reason="dangerous command pattern detected"
                ;;
        esac
        break
    fi
done

if [[ "$blocked" == "true" ]]; then
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    project_path="${PWD:-unknown}"
    echo "[$timestamp] BLOCKED: $command | Reason: $reason | Path: $project_path" >> "$BLOCKED_LOG"
    echo "BLOCKED: $reason"
    echo "Command: $command"
    echo ""
    echo "This command was blocked by your pre-tool-use security hook."
    echo "If you need to run this command, disable the hook temporarily."
    exit 1
fi

exit 0
