#!/usr/bin/env bash
# bash-guard.sh — Pre-tool-use hook that blocks destructive bash commands
# Bounty #3: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
# Author: benjamenhoffman

set -euo pipefail

# Read the command from stdin (Claude Code passes tool input as JSON)
INPUT=$(cat)

# Extract the command field from JSON input
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
  echo '{"decision": "allow", "reason": "No command detected"}'
  exit 0
fi

# Normalize command for checking: trim leading whitespace, get base command
NORMALIZED=$(echo "$COMMAND" | sed 's/^[[:space:]]*//' | tr '[:upper:]' '[:lower:]')

# Get the first word (the actual command)
FIRST_WORD=$(echo "$NORMALIZED" | awk '{print $1}')

# ─────────────────────────────────────────────────
# BLOCKED COMMANDS — Always block these
# ─────────────────────────────────────────────────

# Commands that can destroy data
BLOCKED_COMMANDS=(
  "rm"
  "rmdir"
  "shred"
  "srm"
  "wipe"
  "scrub"
)

# Commands that can modify system state dangerously
BLOCKED_SYSTEM_COMMANDS=(
  "mkfs"
  "dd"
  "fdisk"
  "parted"
  "format"
)

# Package managers that can install/remove software
BLOCKED_PKG_MANAGERS=(
  "apt"
  "apt-get"
  "yum"
  "dnf"
  "pacman"
  "brew"
  "npm"
  "pip"
  "pip3"
  "gem"
  "cargo"
)

# Network commands that can expose data
BLOCKED_NETWORK_COMMANDS=(
  "curl"
  "wget"
  "scp"
  "rsync"
  "ssh"
  "nc"
  "ncat"
  "netcat"
)

# Docker/container commands
BLOCKED_CONTAINER_COMMANDS=(
  "docker"
  "kubectl"
  "podman"
)

# ─────────────────────────────────────────────────
# BLOCKED FLAGS — Block dangerous flags even on allowed commands
# ─────────────────────────────────────────────────

# rm -rf, rm -r, rm -f patterns
if [[ "$FIRST_WORD" == "rm" ]]; then
  if echo "$NORMALIZED" | grep -qE '\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|--recursive|--force)'; then
    echo '{"decision": "block", "reason": "Blocked: rm with recursive and/or force flags can destroy entire directory trees. Use individual file deletions or a trash command instead."}'
    exit 0
  fi
fi

# chmod 777, chmod -R
if [[ "$FIRST_WORD" == "chmod" ]]; then
  if echo "$NORMALIZED" | grep -qE '(777|000|-R\s|--recursive)'; then
    echo '{"decision": "block", "reason": "Blocked: chmod with 777/000 permissions or recursive flag is dangerous. Use specific permissions and targeted paths."}'
    exit 0
  fi
fi

# ─────────────────────────────────────────────────
# BLOCKED PATTERNS — Block dangerous command patterns
# ─────────────────────────────────────────────────

# Pipe to sh/bash (curl | sh pattern)
if echo "$NORMALIZED" | grep -qE '\|\s*(sh|bash|zsh|fish)'; then
  echo '{"decision": "block", "reason": "Blocked: Piping to a shell can execute arbitrary code. Download and inspect scripts before running them."}'
  exit 0
fi

# Redirect to /dev/sd* (disk overwrite)
if echo "$NORMALIZED" | grep -qE '>\s*/dev/sd'; then
  echo '{"decision": "block", "reason": "Blocked: Writing directly to disk devices can destroy data and filesystems."}'
  exit 0
fi

# Sudo with dangerous commands
if [[ "$FIRST_WORD" == "sudo" ]]; then
  SECOND_WORD=$(echo "$NORMALIZED" | awk '{print $2}')
  for cmd in "${BLOCKED_COMMANDS[@]}" "${BLOCKED_SYSTEM_COMMANDS[@]}"; do
    if [[ "$SECOND_WORD" == "$cmd" ]]; then
      echo "{\"decision\": \"block\", \"reason\": \"Blocked: sudo $cmd can cause irreversible system damage.\"}"
      exit 0
    fi
  done
fi

# ─────────────────────────────────────────────────
# CHECK AGAINST BLOCKED LISTS
# ─────────────────────────────────────────────────

for cmd in "${BLOCKED_COMMANDS[@]}"; do
  if [[ "$FIRST_WORD" == "$cmd" ]]; then
    echo "{\"decision\": \"block\", \"reason\": \"Blocked: $cmd is a destructive command that can cause data loss. Use a safer alternative.\"}"
    exit 0
  fi
done

for cmd in "${BLOCKED_SYSTEM_COMMANDS[@]}"; do
  if [[ "$FIRST_WORD" == "$cmd" ]]; then
    echo "{\"decision\": \"block\", \"reason\": \"Blocked: $cmd can modify system partitions or filesystems. Use with explicit approval only.\"}"
    exit 0
  fi
done

for cmd in "${BLOCKED_PKG_MANAGERS[@]}"; do
  if [[ "$FIRST_WORD" == "$cmd" ]]; then
    echo "{\"decision\": \"block\", \"reason\": \"Blocked: $cmd can install or remove software packages. Use with explicit approval only.\"}"
    exit 0
  fi
done

for cmd in "${BLOCKED_NETWORK_COMMANDS[@]}"; do
  if [[ "$FIRST_WORD" == "$cmd" ]]; then
    echo "{\"decision\": \"block\", \"reason\": \"Blocked: $cmd can transfer data to/from remote systems. Use with explicit approval only.\"}"
    exit 0
  fi
done

for cmd in "${BLOCKED_CONTAINER_COMMANDS[@]}"; do
  if [[ "$FIRST_WORD" == "$cmd" ]]; then
    echo "{\"decision\": \"block\", \"reason\": \"Blocked: $cmd can manage containers and their data. Use with explicit approval only.\"}"
    exit 0
  fi
done

# ─────────────────────────────────────────────────
# PATH-BASED PROTECTION — Block writes to critical paths
# ─────────────────────────────────────────────────

CRITICAL_PATHS=(
  "/etc/passwd"
  "/etc/shadow"
  "/etc/sudoers"
  "/boot/"
  "/usr/bin/"
  "/usr/sbin/"
  "/bin/"
  "/sbin/"
  "/var/lib/dpkg/"
  "/var/lib/rpm/"
  "/Library/System/"
  "/System/"
  "C:\\Windows\\"
  "C:\\Program Files\\"
)

for path in "${CRITICAL_PATHS[@]}"; do
  if echo "$NORMALIZED" | grep -qE "(>|>>|cp|mv|ln)\s+.*${path}"; then
    echo "{\"decision\": \"block\", \"reason\": \"Blocked: Writing to critical system path ${path}. Use with explicit approval only.\"}"
    exit 0
  fi
done

# ─────────────────────────────────────────────────
# ENVIRONMENT VARIABLE PROTECTION
# ─────────────────────────────────────────────────

if echo "$NORMALIZED" | grep -qE '(export\s+PATH=|unset\s+PATH)'; then
  echo '{"decision": "block", "reason": "Blocked: Modifying or unsetting PATH can break the shell environment. Use with explicit approval only."}'
  exit 0
fi

# ─────────────────────────────────────────────────
# ALLOW — Command passed all checks
# ─────────────────────────────────────────────────

echo '{"decision": "allow", "reason": "Command does not match any destructive patterns"}'
