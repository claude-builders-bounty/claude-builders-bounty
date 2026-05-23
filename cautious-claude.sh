#!/usr/bin/env bash
# ============================================================
# Cautious Claude — Pre-tool-use hook blocking dangerous bash commands
# Install: cp cautious-claude.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
# ============================================================
set -euo pipefail

readonly LOG_FILE="${HOME}/.claude/hooks/blocked.log"
readonly HOOK_NAME="cautious-claude"

# Ensure log dir exists
mkdir -p "$(dirname "$LOG_FILE")"

# Patterns that are ALWAYS blocked (exact or substring matches)
readonly BLOCK_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf \$HOME"
  "rm -rf /mnt"
  "rm -rf /*"
  "rm -r ~/"
  "rm -rf /boot"
  "rm -rf /etc"
  "rm -rf /usr"
  "rm -rf /var"
  ":(){ :|:& };:"
  "mkfs."
  "dd if=/dev/zero"
  "dd if=/dev/urandom"
  "> /dev/sda"
  "mv / /dev/null"
)

# Patterns that trigger a confirmation check (dangerous but not always malicious)
readonly WARN_PATTERNS=(
  "DROP TABLE"
  "DROP DATABASE"
  "TRUNCATE TABLE"
  "TRUNCATE"
  "DELETE FROM"
  "git push --force"
  "git push -f"
  "chmod 777"
  "chmod -R 777"
  "chown -R"
  "rm -rf"
  "sudo rm"
)

# --- Logging ---
log_blocked() {
  local reason="$1"
  local command="$2"
  local project_path="${3:-unknown}"

  cat >> "$LOG_FILE" << EOF
[$(date '+%Y-%m-%dT%H:%M:%S%z')] BLOCKED [$reason] cmd="$command" project="$project_path"
EOF
}

# --- Parse input ---
# Claude Code sends JSON on stdin for pre-tool-use hooks
input=$(cat)
tool_name=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

# Only intercept bash/ShellToolExecution commands
if [[ "$tool_name" != "bash" && "$tool_name" != "ShellToolExecution" && "$tool_name" != "" ]]; then
  echo '{"continue": true}'
  exit 0
fi

# Extract the command from the input
command_input=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',d.get('command','')))" 2>/dev/null || echo "")
project_path=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd','unknown'))" 2>/dev/null || echo "unknown")

# Normalize: remove extra spaces for pattern matching
command_norm=$(echo "$command_input" | sed 's/[[:space:]]\+/ /g' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

# Skip empty commands
[ -z "$command_norm" ] && { echo '{"continue": true}'; exit 0; }

# --- BLOCK phase: Hard-fail on absolutely dangerous patterns ---
for pattern in "${BLOCK_PATTERNS[@]}"; do
  if [[ "$command_norm" == *"$pattern"* ]] || [[ "$command_norm" =~ $pattern ]]; then
    log_blocked "CRITICAL" "$command_norm" "$project_path"

    cat << EOF | tee >(cat >&2)
================================================================
🚫 BLOCKED — Destructive command intercepted!
================================================================
Command: $command_norm
Matched: $pattern
Reason: This is a system-destroying command that could cause
         irreversible data loss or system failure.
================================================================
If you truly need this, run it manually outside of Claude Code.
================================================================
EOF
    echo '{"continue": false, "reason": "Destructive command blocked: matches critical pattern"}'
    exit 0
  fi
done

# --- WARN phase: Commands that are dangerous but context-dependent ---
for pattern in "${WARN_PATTERNS[@]}"; do
  if [[ "$command_norm" == *"$pattern"* ]]; then
    # Special check: DELETE FROM without WHERE
    if [[ "$pattern" == "DELETE FROM" ]]; then
      if echo "$command_norm" | grep -qi "WHERE"; then
        continue  # Has WHERE clause — safe
      fi
    fi

    # Special check: DROP TABLE / TRUNCATE — always warn
    # Special check: git push --force — always warn

    log_blocked "WARNING" "$command_norm" "$project_path"

    cat << EOF | tee >(cat >&2)
================================================================
⚠️  DANGEROUS COMMAND DETECTED
================================================================
Command: $command_norm
Matched: $pattern
================================================================
This command could cause data loss. Blocked by cautious-claude.

To bypass: export CLAUDE_ALLOW_DANGEROUS=true and retry.
================================================================
EOF
    echo '{"continue": false, "reason": "Dangerous command blocked: matches warning pattern"}'
    exit 0
  fi
done

# --- ALLOW phase ---
echo '{"continue": true}'
