#!/usr/bin/env bash
# pre-tool-use.sh — Claude Code hook that blocks destructive bash commands
# 
# Install: ln -sf $(pwd)/pre-tool-use.sh ~/.claude/hooks/pre-tool-use
# 
# This hook intercepts bash commands before they execute and blocks
# commands that could cause irreversible damage.

set -euo pipefail

# Read the command from stdin (Claude Code hooks receive the command via stdin)
read -r command

# Dangerous patterns that should ALWAYS be blocked
DANGEROUS_PATTERNS=(
  'rm\s+(-rf|--recursive|-fr)\s+/'          # rm -rf /
  'rm\s+(-rf|--recursive|-fr)\s+/\s*$'       # rm -rf / (no trailing)
  'mkfs\.'                                     # Format filesystem
  'dd\s+if=.*\s+of=/dev/'                      # dd to device
  '> /dev/sd'                                   # Direct device write
  'chmod\s+000\s+/'                             # Lock root
  ':\(\)\s*\{.*:\}\s*;.*:'                      # Fork bomb
  'sudo\s+rm\s+-rf\s+/\s*--no-preserve-root'   # sudo rm with force
  'mv\s+/[^ ]+\s+/dev/null'                     # Move to null
  'shutdown\s+-h\s+now'                         # Immediate shutdown
  'halt\s+-f'                                    # Force halt
  'poweroff\s+-f'                                # Force poweroff
  'reboot\s+-f'                                  # Force reboot
  'init\s+0'                                     # Runlevel 0
  'init\s+6'                                     # Runlevel 6
  'wget.*\|.*bash'                               # Pipe download to shell
  'curl.*\|.*bash'                               # Pipe curl to shell
  'git\s+push\s+--force\s+'                      # Force push (often destructive)
  'dbus-send\s+--system.*org\.freedesktop'       # System bus manipulation
)

# Warning patterns (ask for confirmation)
WARNING_PATTERNS=(
  'rm\s+(-rf|--recursive|-fr)'                  # Recursive delete
  'rm\s+-f'                                      # Force delete
  'drop\s+table'                                  # SQL drop
  'drop\s+database'                               # SQL drop database
  'truncate\s+table'                              # SQL truncate
  'ALTER\s+TABLE.*DROP'                           # SQL alter drop
  'git\s+reset\s+--hard'                          # Git hard reset
  'git\s+rebase'                                   # Git rebase
  'git\s+clean\s+-f'                              # Git clean
  'npm\s+publish'                                  # NPM publish
  'npm\s+unpublish'                                # NPM unpublish
  'npm\s+run\s+release'                           # NPM release
  'yarn\s+publish'                                 # Yarn publish
  'gh\s+repo\s+delete'                            # GitHub repo delete
  'aws\s+.*delete'                                 # AWS delete
  'terraform\s+destroy'                            # Terraform destroy
  'kubectl\s+delete'                               # K8s delete
  'docker\s+system\s+prune'                       # Docker prune
  'docker\s+rm\s+.*$(docker\s+ps\s+-aq)'          # Remove all containers
)

# Check against dangerous patterns (uppercase for case-insensitive check)
cmd_upper=$(echo "$command" | tr '[:lower:]' '[:upper:]')

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$command" | grep -qE "$pattern"; then
    echo "{\"blocked\": true, \"reason\": \"Dangerous command blocked: matches pattern '$pattern'. This command could cause irreversible system damage.\"}"
    exit 0
  fi
done

# Check against warning patterns
for pattern in "${WARNING_PATTERNS[@]}"; do
  if echo "$command" | grep -qE "$pattern"; then
    echo "{\"blocked\": true, \"reason\": \"Potentially destructive command detected: '$pattern'. Please confirm this is intentional.\"}"
    exit 0
  fi
done

# Allow the command
echo "{\"blocked\": false}"
