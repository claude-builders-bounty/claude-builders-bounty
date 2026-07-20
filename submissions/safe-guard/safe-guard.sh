#!/usr/bin/env bash
# safe-guard.sh — Pre-execution hook to block destructive bash commands
# Usage: source safe-guard.sh  (in .bashrc/.zshrc)
#    or: bash safe-guard.sh --install  (auto-installs hooks)
#
# Prevents: rm -rf, sudo, chmod 777, fork bombs, disk wipes, and more.

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Blocked command patterns (regex)
BLOCKED_PATTERNS=(
  # File system destruction
  'rm\s+-rf\s+/'
  'rm\s+-rf\s+\/\*'
  'rm\s+-rf\s+\~'
  'rm\s+-rf\s+\$HOME'
  'rm\s+-rf\s+\.\.\/'
  
  # Permission escalation
  'sudo\s+rm'
  'sudo\s+su'
  
  # Permission wide-open
  'chmod\s+777\s+\/'
  'chmod\s+-R\s+777'
  
  # Fork bombs
  ':\(\)\s*\{'
  '\)\(\)\s*\{'
  
  # Disk operations
  'dd\s+if=.*of=\/dev\/sd'
  'mkfs\.'
  'fdisk\s+\/dev\/sd'
  
  # Git destructive
  'git\s+push\s+--force\s+origin\s+(main|master)'
  'git\s+reset\s+--hard\s+HEAD~'
  
  # Dangerous writes
  '>\s+\/dev\/sda'
  '>\s+\/etc\/'
  
  # Systemctl dangerous
  'systemctl\s+disable\s+(ssh|network)'
  
  # Dangerous pip/npm
  'pip\s+uninstall\s+-y'
  'npm\s+uninstall\s+-g'
  
  # Docker destructive
  'docker\s+system\s+prune\s+-af'
  'docker\s+rm\s+-f\s+.*\$\(docker'
)

# Warning-only patterns (not blocked, just warn)
WARN_PATTERNS=(
  'rm\s+-rf\s+\.'
  'rm\s+-rf\s+\*'
  'git\s+push\s+--force'
  'npm\s+publish'
  'docker\s+rmi'
  'pip\s+install\s+.*sudo'
)

BLOCK_COUNT=0
WARN_COUNT=0
OVERRIDE_KEYWORD="I_KNOW_WHAT_IM_DOING"

check_command() {
  local cmd="$1"
  
  # Allow explicit override
  if echo "$cmd" | grep -q "$OVERRIDE_KEYWORD"; then
    return 0
  fi
  
  # Check blocked patterns
  for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$cmd" | grep -qiE "$pattern"; then
      echo -e "${RED}🚫 BLOCKED: Destructive command detected${NC}"
      echo -e "   ${YELLOW}Command:${NC} $cmd"
      echo -e "   ${YELLOW}Matched:${NC} $pattern"
      echo -e "   ${YELLOW}To override:${NC} Prepend '$OVERRIDE_KEYWORD' to your command"
      BLOCK_COUNT=$((BLOCK_COUNT + 1))
      return 1
    fi
  done
  
  # Check warning patterns
  for pattern in "${WARN_PATTERNS[@]}"; do
    if echo "$cmd" | grep -qiE "$pattern"; then
      echo -e "${YELLOW}⚠️  WARNING: Potentially dangerous command${NC}"
      echo -e "   ${YELLOW}Command:${NC} $cmd"
      echo -e "   ${YELLOW}Matched:${NC} $pattern"
      WARN_COUNT=$((WARN_COUNT + 1))
      # Don't block — just warn
    fi
  done
  
  return 0
}

# Install script
install_hooks() {
  local RC_FILE="${1:-$HOME/.zshrc}"
  
  echo -e "${GREEN}Installing safe-guard hooks...${NC}"
  
  SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/safe-guard.sh"
  
  # Add to shell rc
  if ! grep -q "safe-guard.sh" "$RC_FILE" 2>/dev/null; then
    echo "" >> "$RC_FILE"
    echo "# Safe Guard — blocks destructive commands" >> "$RC_FILE"
    echo "source $SCRIPT_PATH" >> "$RC_FILE"
    echo -e "${GREEN}✅ Added to $RC_FILE${NC}"
  else
    echo -e "${YELLOW}Already in $RC_FILE${NC}"
  fi
  
  echo -e "${GREEN}Installed! Restart your shell or run: source $RC_FILE${NC}"
}

# Main
case "${1:-}" in
  --install)
    install_hooks "${2:-}"
    ;;
  --check)
    check_command "${2:-}"
    ;;
  --status)
    echo "Blocked: $BLOCK_COUNT | Warnings: $WARN_COUNT"
    ;;
  --test)
    echo "Testing blocked patterns..."
    for pattern in "${BLOCKED_PATTERNS[@]}"; do
      echo -n "  $pattern → "
      if check_command "echo test: $pattern" 2>/dev/null; then
        echo -e "${GREEN}BLOCKS${NC}"
      else
        echo -e "${RED}MISS${NC}"
      fi
    done
    ;;
  *)
    # When sourced, hook into the shell
    if [[ -n "$BASH_VERSION" ]]; then
      # Bash: use DEBUG trap
      trap 'check_command "$BASH_COMMAND"' DEBUG
    elif [[ -n "$ZSH_VERSION" ]]; then
      # Zsh: use preexec
      preexec() { check_command "$1"; }
    fi
    echo -e "${GREEN}🛡️  Safe Guard active — destructive commands are blocked${NC}"
    echo -e "   ${YELLOW}Use '$OVERRIDE_KEYWORD' prefix to override${NC}"
    ;;
esac
