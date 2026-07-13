#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# safety-hook.sh — Pre-tool-use hook for Claude Code
#
# Intercepts bash commands before execution and blocks/warns on dangerous
# patterns. Supports configurable severity levels, allowlists, scoped rules,
# interactive confirmation, and detailed audit logging.
#
# Protocol (stdin → stdout JSON):
#   Input:  { "type": "tool_use", "name": "bash", "input": { "command": "…" } }
#   Output: { "isBlocked": false }
#        or: { "isBlocked": true, "message": "…" }
#
# Environment variables:
#   SAFETY_HOOK_CONFIG   — path to config YAML (default: <script-dir>/config.yaml)
#   SAFETY_HOOK_LOG      — path to log file    (default: ~/.claude/safety-hook.log)
#   SAFETY_HOOK_CONFIRM  — set to "true"|"1" to auto-confirm all warnings
#   SAFETY_HOOK_DEBUG    — set to "true" for verbose debug logging
#
# Compatibility: bash ≥ 3.2 (macOS default)
# =============================================================================

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR

CONFIG_PATH="${SAFETY_HOOK_CONFIG:-${SCRIPT_DIR}/config.yaml}"
readonly CONFIG_PATH

LOG_DIR="${HOME:?}/.claude"
LOG_FILE="${SAFETY_HOOK_LOG:-${LOG_DIR}/safety-hook.log}"
readonly LOG_DIR LOG_FILE

# ---------------------------------------------------------------------------
# Colours (only when stderr is a terminal)
# ---------------------------------------------------------------------------
if [[ -t 2 ]]; then
  RED='\033[0;31m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'
  BOLD='\033[1m'; GREEN='\033[0;32m'; RESET='\033[0m'
else
  RED=''; YELLOW=''; CYAN=''; BOLD=''; GREEN=''; RESET=''
fi
readonly RED YELLOW CYAN BOLD GREEN RESET

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log_message() {
  local level="$1" message="$2"
  local timestamp; timestamp="$(date '+%Y-%m-%dT%H:%M:%S%z')"
  mkdir -p "$LOG_DIR"
  printf '[%s] [%-5s] %s\n' "$timestamp" "$level" "$message" >> "$LOG_FILE"
}

debug_log() {
  if [[ "${SAFETY_HOOK_DEBUG:-}" == "true" ]]; then
    log_message "DEBUG" "$*"
  fi
}

# ---------------------------------------------------------------------------
# JSON output helpers
# ---------------------------------------------------------------------------
output_blocked() {
  local message="$1"
  message="${message//\\/\\\\}"; message="${message//\"/\\\"}"
  message="${message//$'\n'/\\n}"
  printf '{"isBlocked":true,"message":"%s"}\n' "$message"
  exit 0
}

output_allowed() {
  printf '{"isBlocked":false}\n'
  exit 0
}

output_error() {
  log_message "ERROR" "Hook error: $1"
  printf '{"isBlocked":false}\n'
  exit 0
}

# ---------------------------------------------------------------------------
# JSON input parsing
# ---------------------------------------------------------------------------
parse_stdin() {
  local input tool_name command
  input="$(cat)"
  debug_log "Raw input: ${input:0:500}"

  if command -v python3 &>/dev/null; then
    local parsed
    parsed="$(python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    name = d.get('name', '')
    cmd = d.get('input', {}).get('command', '')
    print(f'{name}|||{cmd}')
except Exception:
    print('|||')
" <<< "$input" 2>/dev/null || echo '|||')"
    tool_name="${parsed%%|||*}"; command="${parsed#*|||}"
  elif command -v python &>/dev/null; then
    local parsed
    parsed="$(python -c "
import sys, json
try:
    d = json.load(sys.stdin)
    name = d.get('name', '')
    cmd = d.get('input', {}).get('command', '')
    print(name + '|||' + cmd)
except Exception:
    print('|||')
" <<< "$input" 2>/dev/null || echo '|||')"
    tool_name="${parsed%%|||*}"; command="${parsed#*|||}"
  else
    tool_name="$(echo "$input" | grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"name"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' || true)"
    command="$(echo "$input" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' || true)"
  fi

  printf '%s|||%s' "$tool_name" "$command"
}

# ---------------------------------------------------------------------------
# Interactive user confirmation
# ---------------------------------------------------------------------------
prompt_user() {
  local message="$1" cmd="$2"

  [[ "$cmd" == *"--dangerous"* ]] && {
    log_message "INFO" "Allowed via --dangerous: ${cmd:0:200}"; return 0
  }

  case "${SAFETY_HOOK_CONFIRM:-}" in
    true|1) log_message "INFO" "Allowed via SAFETY_HOOK_CONFIRM: ${cmd:0:200}"; return 0 ;;
  esac

  if [[ -t 0 && -t 2 ]]; then
    echo "" >&2
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════╗${RESET}" >&2
    echo -e "${YELLOW}║  ${BOLD}⚡  SAFETY HOOK — Potentially Dangerous Command${RESET}${YELLOW}     ║${RESET}" >&2
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════╝${RESET}" >&2
    echo "" >&2
    echo -e "${RED}${message}${RESET}" >&2
    echo "" >&2
    echo -e "${CYAN}Command:${RESET} ${cmd:0:500}" >&2
    echo "" >&2
    echo -e "${BOLD}Options: [y] Allow  [Y] Allow session  [i] Inspect  [n] Block${RESET}" >&2
    echo -n "Proceed? ${BOLD}[y/Y/n/i]${RESET} (n): " >&2
    read -r response </dev/tty || true
    case "${response:-n}" in
      y|Y)
        [[ "$response" == "Y" ]] && { export SAFETY_HOOK_CONFIRM="true"
          echo -e "${YELLOW}→ SAFETY_HOOK_CONFIRM set.${RESET}" >&2; }
        log_message "INFO" "User confirmed: ${cmd:0:200}"; return 0 ;;
      i|I)
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}" >&2
        echo "$cmd" >&2
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}" >&2
        echo -n "Proceed? ${BOLD}[y/n]${RESET} (n): " >&2
        read -r response </dev/tty || true
        case "${response:-n}" in y|Y) log_message "INFO" "User confirmed (inspect): ${cmd:0:200}"; return 0 ;; esac ;;
    esac
    log_message "WARN" "User rejected: ${cmd:0:200}"
    return 1
  fi

  echo "SAFETY HOOK: ${message}" >&2
  echo "Add --dangerous or set SAFETY_HOOK_CONFIRM=true to bypass." >&2
  return 1
}

# ---------------------------------------------------------------------------
# Normalize command for matching
# ---------------------------------------------------------------------------
normalize_cmd() {
  local cmd="$1"
  cmd="${cmd#"${cmd%%[![:space:]]*}"}"
  cmd="${cmd%"${cmd##*[![:space:]]}"}"
  while [[ "$cmd" == *"  "* ]]; do cmd="${cmd//  / }"; done
  echo "$cmd"
}

# ===========================================================================
# BUILT-IN RULES (used when config.yaml is absent)
# ===========================================================================
#
# All patterns use POSIX ERE (Extended Regular Expression):
#   [[:space:]]  instead of \s
#   [|]          for literal pipe (ERE uses | as alternation)
#   [.]          for literal dot
#   No lookaheads, no \b, \d, \w shorthand
#
declare -a RULES_PATTERNS RULES_LEVELS RULES_MESSAGES
declare -a ALLOWLIST_PATTERNS
# Scoped rules format: "scope|directory\0rule_idx\0field\0value"
declare -a SCOPES
DEFAULT_LEVEL="warn"

load_defaults() {
  # pattern | level | message
  RULES_PATTERNS=(
    '^[[:space:]]*rm[[:space:]]+-rf[[:space:]]+/[[:space:]]*$'
    'rm[[:space:]]+-rf[[:space:]]+~([[:space:]]|$)'
    'dd[[:space:]]+if='
    ':[(][)][[:space:]]*[{]'
    '>[[:space:]]+/dev/sd'
    'mkfs[.]'
    'chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+'
    'sudo[[:space:]]+rm[[:space:]]+-rf[[:space:]]+/'
    'sudo[[:space:]]+rm[[:space:]]+-rf[[:space:]]+~'
    'curl[[:space:]]*.*[|].*bash'
    'wget[[:space:]]*.*[|].*sh([^.]|$)'
    'git[[:space:]]+push[[:space:]]+(--force|-f)'
    'drop[[:space:]]+table'
    'delete[[:space:]]+from'
  )
  RULES_LEVELS=(
    block block block block block block block
    block block warn warn warn warn warn
  )
  RULES_MESSAGES=(
    'rm -rf / would destroy the operating system — blocked.'
    'rm -rf ~ would delete the home directory — blocked.'
    'dd if= can overwrite disk devices — blocked.'
    'Fork-bomb detected — blocked.'
    'Direct disk write to /dev/sd* detected — blocked.'
    'mkfs. would format a filesystem — blocked.'
    'chmod -R 777 / makes the entire filesystem world-writable — blocked.'
    'sudo rm -rf / destroys the system as root — blocked.'
    'sudo rm -rf ~ deletes the home directory as root — blocked.'
    'Piping curl to bash is a security risk — allow only if you trust the source.'
    'Piping wget to sh is a security risk — allow only if you trust the source.'
    'Force-push rewrites Git history — confirm to proceed.'
    'DROP TABLE is irreversible — confirm to proceed.'
    'DELETE FROM without WHERE will delete all rows — confirm to proceed.'
  )

  ALLOWLIST_PATTERNS=(
    'npm run build -- --clean'
    'rm -rf node_modules'
    'rm -rf [.]next'
    'rm -rf dist'
    'docker system prune -f'
    'npm run dev -- --clear'
    'cargo clean'
    'make clean'
    'git clean -fd'
    'rm -rf \.cache'
    'rm -rf build'
    'rm -rf target'
  )

  DEFAULT_LEVEL="warn"
}

# ===========================================================================
# Configuration loading
# ===========================================================================
load_config() {
  load_defaults

  [[ -f "$CONFIG_PATH" ]] || {
    log_message "INFO" "No config at ${CONFIG_PATH} — using built-in defaults"
    return 0
  }

  debug_log "Loading config from ${CONFIG_PATH}"

  if command -v python3 &>/dev/null; then
    # Python-based YAML parser (handles most structures)
    python3 -c "
import json, sys, re

try:
    import yaml
except ImportError:
    # Keep it simple — read the file and extract the structure
    # that matches our config format
    import yaml as _yaml  # will fail; fall through to manual parser

class SimpleYAML:
    @staticmethod
    def load(f):
        lines = f.readlines()
        root = {}
        path = [root]
        indent_stack = [-1]
        for line in lines:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            indent = len(line) - len(line.lstrip())
            while indent <= indent_stack[-1]:
                path.pop()
                indent_stack.pop()
            if s.startswith('- '):
                val = s[2:].strip().strip(\"'\").strip('\"')
                parent = path[-1]
                if isinstance(parent, list):
                    parent.append(val)
                continue
            m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_-]*):\s*(.*)', s)
            if m:
                key = m.group(1); val = m.group(2).strip().strip(\"'\").strip('\"')
                cur = path[-1]
                if val:
                    cur[key] = val
                else:
                    new_dict = {}
                    cur[key] = new_dict
                    path.append(new_dict)
                    indent_stack.append(indent)
        return root

yaml = SimpleYAML()
with open('$CONFIG_PATH') as f:
    data = yaml.load(f)

def flatten(obj, prefix=''):
    items = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f'{prefix}.{k}' if prefix else k
            if isinstance(v, (dict, list)):
                items.extend(flatten(v, p))
            else:
                items.append((p, str(v)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            p = f'{prefix}.{i}' if prefix else str(i)
            if isinstance(v, (dict, list)):
                items.extend(flatten(v, p))
            else:
                items.append((p, str(v)))
    return items

flat = flatten(data)
print(json.dumps(flat))
" 2>/dev/null | python3 -c "
import json, sys
try:
    for k, v in json.load(sys.stdin):
        print(f'{k}={v}')
except Exception:
    pass
" 2>/dev/null | while IFS='=' read -r key val; do
      apply_config_kv "$key" "$val"
    done
    log_message "INFO" "Config loaded from ${CONFIG_PATH}"
  else
    # Grep-based fallback for minimal YAML parsing
    parse_yaml_grep "$CONFIG_PATH"
    log_message "INFO" "Config loaded (grep) from ${CONFIG_PATH}"
  fi
}

# ---------------------------------------------------------------------------
# Apply config key=value pair (called from Python YAML parser)
# ---------------------------------------------------------------------------
apply_config_kv() {
  local key="$1" val="$2"

  case "$key" in
    safety_hook.default_level) DEFAULT_LEVEL="$val" ;;

    rules.*.pattern)
      local idx="${key#rules.}"; idx="${idx%.pattern}"
      while (( ${#RULES_PATTERNS[@]} <= idx )); do
        RULES_PATTERNS[${#RULES_PATTERNS[@]}]=""
        RULES_LEVELS[${#RULES_LEVELS[@]}]=""
        RULES_MESSAGES[${#RULES_MESSAGES[@]}]=""
      done
      RULES_PATTERNS[$idx]="$val" ;;

    rules.*.level)
      local idx="${key#rules.}"; idx="${idx%.level}"
      RULES_LEVELS[$idx]="$val" ;;

    rules.*.message)
      local idx="${key#rules.}"; idx="${idx%.message}"
      RULES_MESSAGES[$idx]="$val" ;;

    allowlist.*)
      local idx="${key#allowlist.}"
      ALLOWLIST_PATTERNS[$idx]="$val" ;;

    scoped_rules.*.directory)
      local idx="${key#scoped_rules.}"; idx="${idx%.directory}"
      SCOPES[${#SCOPES[@]}]="scope|${idx}|${val}" ;;

    scoped_rules.*.rules.*.pattern)
      local rest="${key#scoped_rules.}"
      local sidx="${rest%%.*}"; local tmp="${rest#*.rules.}"
      local ridx="${tmp%.pattern}"
      SCOPES[${#SCOPES[@]}]="rule|${sidx}|${ridx}|pattern|${val}" ;;

    scoped_rules.*.rules.*.level)
      local rest="${key#scoped_rules.}"
      local sidx="${rest%%.*}"; local tmp="${rest#*.rules.}"
      local ridx="${tmp%.level}"
      SCOPES[${#SCOPES[@]}]="rule|${sidx}|${ridx}|level|${val}" ;;

    scoped_rules.*.rules.*.message)
      local rest="${key#scoped_rules.}"
      local sidx="${rest%%.*}"; local tmp="${rest#*.rules.}"
      local ridx="${tmp%.message}"
      SCOPES[${#SCOPES[@]}]="rule|${sidx}|${ridx}|message|${val}" ;;
  esac
}

# ---------------------------------------------------------------------------
# Grep-based YAML fallback parser
# ---------------------------------------------------------------------------
parse_yaml_grep() {
  local file="$1"
  local in_rules=false in_allowlist=false in_scoped=false
  local scope_key="" scope_ridx=0

  while IFS= read -r line || [[ -n "$line" ]]; do
    local trimmed="${line##+([[:space:]])}"
    [[ -z "$trimmed" || "$trimmed" == \#* ]] && continue

    case "$trimmed" in
      rules:)        in_rules=true; in_allowlist=false; in_scoped=false; continue ;;
      allowlist:)    in_rules=false; in_allowlist=true; in_scoped=false; continue ;;
      scoped_rules:) in_rules=false; in_allowlist=false; in_scoped=true; continue ;;
      safety_hook:)  in_rules=false; in_allowlist=false; in_scoped=false; continue ;;
    esac

    if $in_scoped; then
      if [[ "$trimmed" =~ ^-\ directory:\ (.*) ]]; then
        scope_key="${BASH_REMATCH[1]}"
        scope_key="${scope_key#\"}"; scope_key="${scope_key%\"}"
        scope_key="${scope_key#\'}"; scope_key="${scope_key%\'}"
        scope_ridx=0
        continue
      fi
      [[ "$trimmed" == "rules:" ]] && continue
      if [[ "$trimmed" =~ ^-\ pattern:\ (.*) ]]; then
        local v="${BASH_REMATCH[1]}"
        v="${v#\"}"; v="${v%\"}"; v="${v#\'}"; v="${v%\'}"
        SCOPES[${#SCOPES[@]}]="rule|${scope_key}|${scope_ridx}|pattern|${v}"
        continue
      fi
      if [[ "$trimmed" =~ ^level:\ (.*) ]]; then
        SCOPES[${#SCOPES[@]}]="rule|${scope_key}|${scope_ridx}|level|${BASH_REMATCH[1]}"
        continue
      fi
      if [[ "$trimmed" =~ ^message:\ (.*) ]]; then
        local v="${BASH_REMATCH[1]}"
        v="${v#\"}"; v="${v%\"}"; v="${v#\'}"; v="${v%\'}"
        SCOPES[${#SCOPES[@]}]="rule|${scope_key}|${scope_ridx}|message|${v}"
        ((scope_ridx++))
        continue
      fi
      continue
    fi

    if $in_rules; then
      if [[ "$trimmed" =~ ^-\ pattern:\ (.*) ]]; then
        local ptrn="${BASH_REMATCH[1]}"
        ptrn="${ptrn#\"}"; ptrn="${ptrn%\"}"; ptrn="${ptrn#\'}"; ptrn="${ptrn%\'}"
        RULES_PATTERNS[${#RULES_PATTERNS[@]}]="$ptrn"
        RULES_LEVELS[${#RULES_LEVELS[@]}]=""; RULES_MESSAGES[${#RULES_MESSAGES[@]}]=""
        continue
      fi
      if [[ "$trimmed" =~ ^level:\ (.*) ]]; then
        local idx=$(( ${#RULES_PATTERNS[@]} - 1 ))
        (( idx >= 0 )) && RULES_LEVELS[$idx]="${BASH_REMATCH[1]}"
        continue
      fi
      if [[ "$trimmed" =~ ^message:\ (.*) ]]; then
        local msg="${BASH_REMATCH[1]}"
        msg="${msg#\"}"; msg="${msg%\"}"; msg="${msg#\'}"; msg="${msg%\'}"
        local idx=$(( ${#RULES_PATTERNS[@]} - 1 ))
        (( idx >= 0 )) && RULES_MESSAGES[$idx]="$msg"
        continue
      fi
      continue
    fi

    if $in_allowlist; then
      if [[ "$trimmed" =~ ^-\ (.*) ]]; then
        local val="${BASH_REMATCH[1]}"
        val="${val#\"}"; val="${val%\"}"; val="${val#\'}"; val="${val%\'}"
        ALLOWLIST_PATTERNS[${#ALLOWLIST_PATTERNS[@]}]="$val"
      fi
      continue
    fi

    if [[ "$trimmed" =~ ^default_level:\ (.*) ]]; then
      DEFAULT_LEVEL="${BASH_REMATCH[1]}"
    fi
  done < "$file"
}

# ===========================================================================
# Allowlist check
# ===========================================================================
check_allowlist() {
  local cmd="$1" p
  debug_log "Allowlist: ${#ALLOWLIST_PATTERNS[@]} entries"
  for p in "${ALLOWLIST_PATTERNS[@]:+${ALLOWLIST_PATTERNS[@]}}"; do
    [[ -z "$p" ]] && continue
    if [[ "$cmd" =~ $p ]]; then
      debug_log "Allowlist match: '${p}'"
      log_message "INFO" "Allowlist: cmd='${cmd:0:200}' pattern='${p}'"
      return 0
    fi
  done
  return 1
}

# ===========================================================================
# Scoped rules check
# ===========================================================================
check_scoped_rules() {
  local cmd="$1" cwd
  cwd="$(pwd 2>/dev/null || echo "${HOME}")"

  # Build list of unique scope directories from SCOPES
  local -a dirs=()
  local e
  for e in "${SCOPES[@]:+${SCOPES[@]}}"; do
    if [[ "$e" == scope\|* ]]; then
      local d="${e#scope|}"
      d="${d#*|}"  # after scope|idx|
      dirs[${#dirs[@]}]="$d"
    fi
  done

  for scope_dir in "${dirs[@]:+${dirs[@]}}"; do
    [[ "$cwd" != "$scope_dir" && "$cwd" != "$scope_dir"/* ]] && continue

    # Gather rules for this scope
    local -a sp=() sl=() sm=()
    for e in "${SCOPES[@]:+${SCOPES[@]}}"; do
      if [[ "$e" == rule\|* ]]; then
        local rest="${e#rule|}"
        local d="${rest%%|*}"; rest="${rest#*|}"
        local ridx="${rest%%|*}"; rest="${rest#*|}"
        local field="${rest%%|*}"; local val="${rest#*|}"
        [[ "$d" != "$scope_dir" ]] && continue
        case "$field" in
          pattern) sp[$ridx]="$val" ;;
          level)   sl[$ridx]="$val" ;;
          message) sm[$ridx]="$val" ;;
        esac
      fi
    done

    for (( ri=0; ri<${#sp[@]}; ri++ )); do
      local p="${sp[$ri]:-}"; [[ -z "$p" ]] && continue
      [[ "$cmd" =~ $p ]] || continue
      local msg="${sm[$ri]:-Command matched scoped rule}"
      local sev="${sl[$ri]:-$DEFAULT_LEVEL}"
      log_message "MATCH" "Scoped [${scope_dir}#${ri}]: ${cmd:0:200}"
      echo "${YELLOW}${BOLD}⚡  SAFETY HOOK (${scope_dir}): ${msg}${RESET}" >&2
      case "$sev" in
        block) log_message "BLOCK" "Scoped block: ${cmd:0:200}"; output_blocked "$msg" ;;
        *)     log_message "SCOPED_ALLOW" "Scoped allow: ${cmd:0:200}"; return 0 ;;
      esac
    done
  done

  return 1
}

# ===========================================================================
# Global rules check
# ===========================================================================
check_rules() {
  local cmd="$1" i

  for (( i=0; i<${#RULES_PATTERNS[@]}; i++ )); do
    local pattern="${RULES_PATTERNS[$i]:-}"
    local level="${RULES_LEVELS[$i]:-$DEFAULT_LEVEL}"
    local message="${RULES_MESSAGES[$i]:-Command matched pattern}"

    [[ -z "$pattern" ]] && continue
    debug_log "Rule #${i}: pattern='${pattern}' level='${level}'"

    if [[ "$cmd" =~ $pattern ]]; then
      log_message "MATCH" "Rule #${i}: ${cmd:0:200} matched '${pattern}' level='${level}'"

      # "delete from" needs WHERE clause to be safe
      if [[ "$pattern" == *delete*from* ]]; then
        if [[ "$cmd" =~ [Ww][Hh][Ee][Rr][Ee] ]]; then
          debug_log "Rule #${i}: has WHERE — skipping"
          continue
        fi
      fi

      case "$level" in
        block)
          echo "${RED}${BOLD}⛔  ${message}${RESET}" >&2
          log_message "BLOCK" "Blocked: ${cmd:0:200}"
          output_blocked "$message"
          ;;
        warn|allow_with_confirmation)
          echo "${YELLOW}${BOLD}⚡  ${message}${RESET}" >&2
          if prompt_user "$message" "$cmd"; then
            log_message "ALLOW" "Warn allowed: ${cmd:0:200}"; return 0
          else
            log_message "BLOCK" "Warn rejected: ${cmd:0:200}"
            output_blocked "Command rejected by user: ${message}"
          fi
          ;;
        allow)
          log_message "INFO" "Allow-level: ${cmd:0:200}"; return 0
          ;;
        *)  log_message "WARN" "Unknown level '${level}'; treating as warn"
          prompt_user "$message" "$cmd" || output_blocked "Command rejected: ${message}"
          return 0 ;;
      esac
    fi
  done

  return 0
}

# ===========================================================================
# Main
# ===========================================================================
main() {
  load_config

  local parsed tool_name command
  parsed="$(parse_stdin)"
  tool_name="${parsed%%|||*}"; command="${parsed#*|||}"

  debug_log "Parsed: tool='${tool_name}'"

  # Only process bash tool calls
  [[ "$tool_name" != "bash" || -z "$command" ]] && output_allowed

  command="$(normalize_cmd "$command")"

  # Strip leading newlines/semicolons/spaces
  while [[ "$command" == [$'\n\r;\t ']* ]]; do
    command="${command##[$'\n\r;\t ']}"
  done

  [[ -z "$command" ]] && output_allowed
  debug_log "Normalized: '${command:0:300}'"

  # 1. Allowlist
  check_allowlist "$command" && { log_message "PASS" "Allowlist: ${command:0:200}"; output_allowed; }

  # 2. Scoped rules
  check_scoped_rules "$command" && { log_message "PASS" "Scoped: ${command:0:200}"; output_allowed; }

  # 3. Global rules
  check_rules "$command"

  # 4. No match
  log_message "PASS" "No rules: ${command:0:200}"
  output_allowed
}

trap 'output_error "Unexpected error at line $LINENO"' ERR
main "$@"
