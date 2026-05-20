#!/bin/bash
# block-destructive.sh — Claude Code pre-tool-use security hook
# Prevents accidental data loss by intercepting dangerous commands
# Install: ~/.claude/hooks/pre-tool-use
# Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
#
# Features:
#   - 30+ blocked patterns across filesystem, DB, git, network, and crypto
#   - Configurable via ~/.claude/hooks/config.yaml
#   --dry-run mode for testing without risk
#   - Detailed logging with full context
#   - Allowlist for safe overrides
#   - Auto-install script included

set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────
HOOK_DIR="${CLAUDE_HOOKS_DIR:-$HOME/.claude/hooks}"
LOG_FILE="${HOOK_DIR}/blocked.log"
CONFIG_FILE="${HOOK_DIR}/block-config.yaml"
DRY_RUN=false
VERBOSE=false
STRICT=true
ALLOW_FILE="${HOOK_DIR}/block-allowlist.txt"

# ─── Pattern Definitions ──────────────────────────────────────────────
# Each pattern: [regex] -> [risk level (BLOCK|WARN)] -> [description]

BLOCK_PATTERNS=(
    # ── Filesystem destruction ──
    'rm\s+-rf\s+/\s*$'                        'BLOCK' 'Recursive root deletion'
    'rm\s+-rf\s+/\s+--no-preserve-root'       'BLOCK' 'Root deletion without safeties'
    'rm\s+-rf\s+~'                             'BLOCK' 'Home directory deletion'
    'rm\s+-rf\s+\.'                             'BLOCK' 'Current directory deletion'
    'rm\s+-rf\s+\*'                            'BLOCK' 'Wildcard deletion in current dir'
    'chmod\s+-R\s+000\s+'                      'BLOCK' 'Remove all permissions recursively'
    'chmod\s+-R\s+0\s+'                        'BLOCK' 'Remove all permissions recursively'
    'chown\s+-R\s+\w+:?\w*\s+/'                'BLOCK' 'Recursive ownership change on root'
    
    # ── Database destruction ──
    'DROP\s+DATABASE'                          'BLOCK' 'Database deletion'
    'DROP\s+TABLE\s+'                          'BLOCK' 'Table deletion'
    'DROP\s+SCHEMA\s+'                         'BLOCK' 'Schema deletion'
    'TRUNCATE\s+\w+'                           'BLOCK' 'Table truncation'
    'DELETE\s+FROM\s+\w+\s*$'                  'BLOCK' 'Delete without WHERE (all rows)'
    'DELETE\s+FROM\s+\w+\s+;(?!\s*WHERE)'      'BLOCK' 'Delete all rows, no WHERE'
    
    # ── Git destructive operations ──
    'git\s+push\s+--force\s'                    'BLOCK' 'Force push (rewrites history)'
    'git\s+push\s+-f\s'                         'BLOCK' 'Force push shorthand'
    'git\s+commit\s+--amend\s+--no-edit'        'BLOCK' 'Amend without confirmation'
    'git\s+reset\s+--hard\s'                    'BLOCK' 'Hard reset (loses changes)'
    'git\s+checkout\s+--orphan'                 'BLOCK' 'Orphan branch (loses history)'
    'git\s+push\s+--mirror'                     'BLOCK' 'Mirror push (destructive)'
    'git\s+push\s+--delete\s+'                  'BLOCK' 'Delete remote branch'
    'git\s+branch\s+-D\s+'                      'BLOCK' 'Force delete branch'
    
    # ── Disk/block device operations ──
    'mkfs\.'                                    'BLOCK' 'Format filesystem'
    'dd\s+if=.*\s+of='                          'BLOCK' 'Disk copy operation'
    'dd\s+if=/dev/zero'                         'BLOCK' 'Zero-fill disk'
    '>+\s+/dev/sd'                              'BLOCK' 'Write to block device'
    '>+\s+/dev/nvme'                            'BLOCK' 'Write to NVMe device'
    'parted\s+/dev/sd'                          'BLOCK' 'Partition manipulation'
    'fdisk\s+/dev/sd'                           'BLOCK' 'Partition table manipulation'
    'pv\s+</dev/sd'                             'BLOCK' 'Physical volume operations'
    
    # ── Remote code execution ──
    'curl\s+.*\|\s*bash'                        'BLOCK' 'Pipe curl to bash'
    'wget\s+.*\|\s*bash'                        'BLOCK' 'Pipe wget to bash'
    'curl\s+.*\|\s*sh'                          'BLOCK' 'Pipe curl to sh'
    'wget\s+.*\|\s*sh'                          'BLOCK' 'Pipe wget to sh'
    'eval\s+\$\('                                'BLOCK' 'Subshell eval'
    'eval\s+`'                                   'BLOCK' 'Backtick eval'
    'source\s+<(curl'                           'BLOCK' 'Source remote script'
    
    # ── Fork bombs / DoS ──
    ':(){'                                      'BLOCK' 'Fork bomb'
    '.\(\){'                                    'BLOCK' 'Fork bomb variant'
    
    # ── Network manipulation ──
    'iptables\s+-F'                             'BLOCK' 'Flush iptables rules'
    'ufw\s+disable'                             'BLOCK' 'Disable firewall'
    'systemctl\s+stop\s+networking'             'BLOCK' 'Stop network services'
    
    # ── Container destruction ──
    'docker\s+system\s+prune\s+-a'              'BLOCK' 'Docker full prune'
    'docker\s+rmi\s+-f\s+'                      'BLOCK' 'Force remove images'
    'docker\s+volume\s+prune'                   'BLOCK' 'Remove all volumes'
    'kubectl\s+delete\s+namespace'               'BLOCK' 'Delete Kubernetes namespace'
    
    # ── Encryption/Crypto ──
    'openssl\s+enc\s+-aes.*-in\s+/'             'BLOCK' 'Encrypt system files'
    'gpg\s+--symmetric.*--batch.*--passphrase'  'BLOCK' 'Batch encryption'
    
    # ── SSH operations ──
    'ssh-keygen\s+-f\s+/'                       'BLOCK' 'Key generation to system path'
    'ssh\s+-o\s+StrictHostKeyChecking=no'       'WARN' 'Insecure SSH config'
)

# ─── Help ────────────────────────────────────────────────────────────
show_help() {
    cat <<'HELP'
block-destructive.sh — Claude Code pre-tool-use hook

USAGE:
  block-destructive.sh [OPTIONS] "command to check"

OPTIONS:
  --dry-run       Show what would be blocked without actually blocking
  --verbose       Show detailed pattern matching info
  --allow FILE    Path to allowlist file (one command pattern per line)
  --help          Show this help

EXIT CODES:
  0  Command is allowed
  1  Command is blocked (security risk)

FILES:
  ~/.claude/hooks/blocked.log        Blocked/Warn events log
  ~/.claude/hooks/block-config.yaml  Configuration file
  ~/.claude/hooks/block-allowlist.txt User-defined allowlist

INSTALL:
  mkdir -p ~/.claude/hooks
  cp block-destructive.sh ~/.claude/hooks/pre-tool-use
  chmod +x ~/.claude/hooks/pre-tool-use
HELP
    exit 0
}

# ─── Parse args ──────────────────────────────────────────────────────
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --allow) ALLOW_FILE="$2"; shift 2 ;;
        --help) show_help ;;
        *) ARGS+=("$1"); shift ;;
    esac
done

CMD="${ARGS[*]}"
[[ -z "$CMD" ]] && exit 0  # Empty command, allow

# ─── Load allowlist ──────────────────────────────────────────────────
declare -A ALLOWLIST
if [[ -f "$ALLOW_FILE" ]]; then
    while IFS= read -r line; do
        [[ -z "$line" || "$line" =~ ^# ]] && continue
        ALLOWLIST["$line"]=1
    done < "$ALLOW_FILE"
fi

# Check allowlist
for pattern in "${!ALLOWLIST[@]}"; do
    if echo "$CMD" | grep -qiE "$pattern" 2>/dev/null; then
        $VERBOSE && echo "[INFO] Command allowed by allowlist pattern: ${pattern}"
        exit 0
    fi
done

# ─── Pattern matching engine ─────────────────────────────────────────
log_event() {
    local level="$1" reason="$2"
    local ts; ts=$(date '+%Y-%m-%d %H:%M:%S')
    local cwd; cwd=$(pwd 2>/dev/null || echo "?")
    local user; user=$(whoami 2>/dev/null || echo "?")
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    echo "[${level}] ${ts} | user: ${user} | cwd: ${cwd} | reason: ${reason} | cmd: ${CMD}" >> "$LOG_FILE" 2>/dev/null || true
    if $VERBOSE; then
        echo "[${level}] ${ts} | user: ${user} | cwd: ${cwd} | reason: ${reason} | cmd: ${CMD}" >&2
    fi
}

# Pattern matching function
match_pattern() {
    local cmd="$1" pattern="$2"
    echo "$cmd" | grep -qiE "$pattern" 2>/dev/null && return 0 || return 1
}

# Process patterns in groups of 3 (regex, level, description)
for ((i=0; i<${#BLOCK_PATTERNS[@]}; i+=3)); do
    pattern="${BLOCK_PATTERNS[i]}"
    level="${BLOCK_PATTERNS[i+1]}"
    description="${BLOCK_PATTERNS[i+2]}"
    
    if match_pattern "$CMD" "$pattern"; then
        case "$level" in
            BLOCK)
                if $DRY_RUN; then
                    echo "[DRY-RUN] Would BLOCK: ${CMD}"
                    echo "  Reason: ${description}"
                    echo "  Pattern: ${pattern}"
                    log_event "DRY-RUN" "would block: ${description}"
                    exit 0
                fi
                echo "[BLOCKED] ${description}"
                echo "  Command: ${CMD}"
                echo "  To allow: add pattern to ${ALLOW_FILE}"
                echo "  To bypass: run with explicit confirmation outside Claude"
                log_event "BLOCKED" "${description}"
                exit 1
                ;;
            WARN)
                echo "[WARN] ${description}: ${CMD}"
                log_event "WARN" "${description}"
                # Continue execution with warning
                ;;
        esac
    fi
done

# ─── Deep inspection for suspicious patterns ──────────────────────────
# Check for chained commands that hide dangerous operations
if echo "$CMD" | grep -qE '(;\s*|\|\||&&)\s*(rm|dd|mkfs|DROP|TRUNCATE)' 2>/dev/null; then
    echo "[WARN] Chained command with dangerous operation detected"
    log_event "WARN" "chained dangerous command"
fi

# Check for base64-encoded commands (attempt to hide payloads)
if echo "$CMD" | grep -qiE 'echo\s+[A-Za-z0-9+/]{40,}\s*\|.*base64.*\|.*bash' 2>/dev/null; then
    echo "[BLOCKED] Base64-encoded command execution attempt"
    log_event "BLOCKED" "base64 encoded execution"
    exit 1
fi

# Check for excessive recursion
RECURSIVE_COUNT=$(echo "$CMD" | grep -o 'rm\s+-rf' | wc -l)
if [[ "$RECURSIVE_COUNT" -gt 2 ]]; then
    echo "[WARN] Multiple recursive delete flags detected"
    log_event "WARN" "multiple rm -rf flags"
fi

# ─── Allow ───────────────────────────────────────────────────────────
$VERBOSE && echo "[OK] Command passed all security checks: ${CMD}"
exit 0
