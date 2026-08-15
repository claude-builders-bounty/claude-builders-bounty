#!/usr/bin/env bash
# ==============================================================================
# Hook: block-destructive.sh
# Purpose: Intercepts & blocks destructive or catastrophic shell commands
# Compatible with: Claude Code PreToolUse hooks, bash pre-exec wrappers, CI/CD
# ==============================================================================

set -euo pipefail

# Combine all arguments as the full command string, or read from standard input if empty
COMMAND_STR="$*"
if [[ -z "$COMMAND_STR" && ! -t 0 ]]; then
    COMMAND_STR=$(cat)
fi

# Trim leading/trailing whitespace
COMMAND_STR="$(echo -e "${COMMAND_STR}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

if [[ -z "$COMMAND_STR" ]]; then
    exit 0
fi

# Function to block command with warning and exit 1
block_command() {
    local reason="$1"
    echo "🚨 [BLOCKED] Destructive command intercepted by safety hook!" >&2
    echo "Reason: ${reason}" >&2
    echo "Target: ${COMMAND_STR}" >&2
    echo "If this action is intentional, check hooks/README.md for override instructions." >&2
    exit 1
}

# ------------------------------------------------------------------------------
# 1. Catastrophic / Root / Broad File System Deletion
# ------------------------------------------------------------------------------
# Matches rm (-options) targeting /, ~, *, /*, ~/*, etc.
if echo "$COMMAND_STR" | grep -iE '\brm[[:space:]]+(-[a-zA-Z0-9]*r[a-zA-Z0-9]*f?[a-zA-Z0-9]*|-[a-zA-Z0-9]*f[a-zA-Z0-9]*r[a-zA-Z0-9]*|[[:space:]]+-r[[:space:]]+-f|[[:space:]]+-f[[:space:]]+-r)[[:space:]]+(\/|\/\*|~|~\/|\*|\.\/|\.\/\*|\.\.|\.\.\/\*)([[:space:]]+|$)' >/dev/null 2>&1; then
    block_command "Unscoped or root-level recursive file deletion (e.g. rm -rf /, ~, *, ..)"
fi

# Exact pattern check for rm variations on root/wildcard
if echo "$COMMAND_STR" | grep -iE '\brm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*[[:space:]]+.*(\/|\/\*|~|~\/|\*|\.\/|\.\/\*)([[:space:]]|$)' >/dev/null 2>&1; then
    # Double check if it is deleting root/home/wildcard
    if echo "$COMMAND_STR" | grep -iE '\brm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*[[:space:]]+([[:space:]]*(\/|\/\*|~|~\/|\*|\.\.|\.\/\*)[[:space:]]*)+$' >/dev/null 2>&1; then
        block_command "Unscoped or root-level recursive file deletion"
    fi
fi

# ------------------------------------------------------------------------------
# 2. Forced Git Pushes to Protected Production Branches
# ------------------------------------------------------------------------------
# Matches git push -f / --force / --force-with-lease to main, master, prod, production
if echo "$COMMAND_STR" | grep -iE '\bgit[[:space:]]+push[[:space:]]+.*(-f\b|--force\b|--force-with-lease\b)[[:space:]]+.*(origin[[:space:]]+)?(main|master|prod|production)\b' >/dev/null 2>&1 || \
   echo "$COMMAND_STR" | grep -iE '\bgit[[:space:]]+push[[:space:]]+.*(origin[[:space:]]+)?(main|master|prod|production)[[:space:]]+.*(-f\b|--force\b|--force-with-lease\b)' >/dev/null 2>&1 || \
   echo "$COMMAND_STR" | grep -iE '\bgit[[:space:]]+push[[:space:]]+.*(\+main|\+master|\+prod|\+production)\b' >/dev/null 2>&1; then
    block_command "Force pushing to protected branch (main/master/prod)"
fi

# ------------------------------------------------------------------------------
# 3. Raw Disk Formatting, Overwrites & Direct Device Writes
# ------------------------------------------------------------------------------
# Matches mkfs, fdisk destructive modes, dd writing to raw disks (/dev/sd*, /dev/nvme*, /dev/disk*, /dev/hd*)
if echo "$COMMAND_STR" | grep -iE '\bmkfs(\.[a-zA-Z0-9_-]+)?[[:space:]]+' >/dev/null 2>&1; then
    block_command "Filesystem formatting tool (mkfs) detected"
fi

if echo "$COMMAND_STR" | grep -iE '\bdd[[:space:]]+.*of=\/dev\/(sd[a-z]|hd[a-z]|nvme[0-9]n[0-9]|disk[0-9]|rdisk[0-9]|mapper|null|zero)' >/dev/null 2>&1; then
    if echo "$COMMAND_STR" | grep -iE '\bdd[[:space:]]+.*of=\/dev\/(sd[a-z]|hd[a-z]|nvme[0-9]n[0-9]|disk[0-9]|rdisk[0-9]|mapper)' >/dev/null 2>&1; then
        block_command "Direct disk write via dd (of=/dev/...) detected"
    fi
fi

# ------------------------------------------------------------------------------
# 4. Recursive Permission Wipeout on Root / System Directories
# ------------------------------------------------------------------------------
# Matches chmod -R 777 / or chmod -R 000 / or chown -R on / or /etc /var /usr
if echo "$COMMAND_STR" | grep -iE '\bchmod[[:space:]]+.*-R[[:space:]]+[0-7]{3,4}[[:space:]]+(\/|\/etc|\/var|\/usr|\/bin|\/sbin|\/System|\/Library)([[:space:]]+|$)' >/dev/null 2>&1 || \
   echo "$COMMAND_STR" | grep -iE '\bchown[[:space:]]+.*-R[[:space:]]+[a-zA-Z0-9_:-]+[[:space:]]+(\/|\/etc|\/var|\/usr|\/bin|\/sbin|\/System|\/Library)([[:space:]]+|$)' >/dev/null 2>&1; then
    block_command "Recursive system permission/ownership modification on root directory"
fi

# ------------------------------------------------------------------------------
# 5. Dangerous SQL Drop / Truncate Commands
# ------------------------------------------------------------------------------
# Matches raw DROP DATABASE, DROP TABLE without qualification or in inline commands
if echo "$COMMAND_STR" | grep -iE '(DROP[[:space:]]+DATABASE\b|DROP[[:space:]]+SCHEMA\b|TRUNCATE[[:space:]]+TABLE\b|DROP[[:space:]]+TABLE\b)' >/dev/null 2>&1; then
    block_command "Destructive SQL operation (DROP DATABASE/TABLE/SCHEMA or TRUNCATE) detected"
fi

# ------------------------------------------------------------------------------
# 6. System Shutdown / Fork Bomb / Wipe Utilities
# ------------------------------------------------------------------------------
if echo "$COMMAND_STR" | grep -F ':(){ :|:& };:' >/dev/null 2>&1 || \
   echo "$COMMAND_STR" | grep -iE '(\bshutdown\b|\binit[[:space:]]+0\b|\breboot\b|\bhalt\b|\bpoweroff\b)' >/dev/null 2>&1; then
    block_command "System shutdown, reboot, or fork bomb command detected"
fi

# Command is safe according to hook policies
exit 0
