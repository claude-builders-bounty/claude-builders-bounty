#!/usr/bin/env bash
# destructive-bash-hook.sh - PreToolUse hook for Claude Code
# Blocks destructive bash commands before execution.
#
# Usage:
#   bash destructive-bash-hook.sh "<command>"
#
# Returns exit code 0 if command is safe, 1 if blocked.
# Prints "BLOCKED: ..." to stderr on block.

set -euo pipefail

COMMAND="${1:-}"
LOWER="$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')"

block() {
  local reason="$1"
  echo "BLOCKED: destructive command detected - reason: ${reason}" >&2
  echo "Allowed: false" >&2
  exit 1
}

# 1. rm -rf on root or home
if echo "$LOWER" | grep -Eq '(rm\s+.*-rf\s+(/|~|/\*|\$HOME|/home|/etc|/bin|/sbin|/usr|/var|/root|/boot|/dev|/proc|/sys|/tmp|/opt|/usr/local|/mnt|/media|/srv|/run|/lib|/lib64))'; then
  block "rm -rf on root directory or system path"
fi

# 2. rm -rf .git
if echo "$LOWER" | grep -Eq 'rm\s+.*-rf\s+(\.git|\.git/)'; then
  block "rm -rf .git directory"
fi

# 3. mkfs (format disk)
if echo "$LOWER" | grep -Eq 'mkfs\.'; then
  block "mkfs disk formatting"
fi

# 4. dd writing to block device
if echo "$LOWER" | grep -Eq 'dd\s+.*of\s*=\s*/dev/(sd|hd|vd|xvd|nvme|mmcblk)'; then
  block "dd writing to block device"
fi

# 5. Fork bomb
if echo "$LOWER" | grep -Eq ':\(\)\s*\{.*:.*&\};:'; then
  block "fork bomb pattern"
fi

# 6. chmod -R 777 on system paths
if echo "$LOWER" | grep -Eq 'chmod\s+.*-R\s+777\s+(/|~|/\*|\$HOME|/etc|/bin|/sbin|/usr|/var|/root|/boot|/dev|/proc|/sys|/opt|/mnt|/media|/srv|/run|/lib|/lib64)'; then
  block "chmod -R 777 on system path"
fi

# 7. Redirect to block device
if echo "$LOWER" | grep -Eq '>\s*/dev/(sd|hd|vd|xvd|nvme|mmcblk)'; then
  block "redirect to block device"
fi

# 8. System shutdown/halt
if echo "$LOWER" | grep -Eq '^(shutdown|halt|poweroff|init\s+0|reboot)'; then
  block "system shutdown or reboot"
fi

# 9. git push --force on protected branches
if echo "$LOWER" | grep -Eq 'git\s+push.*--force.*(main|master|production|main)'; then
  block "force push to protected branch"
fi

# 10. truncate system files
if echo "$LOWER" | grep -Eq '(>|>>)\s*/etc/(passwd|shadow|group|hosts|fstab|sudoers)'; then
  block "truncate system config file"
fi

exit 0
