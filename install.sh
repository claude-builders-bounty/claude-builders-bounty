#!/bin/bash
# Claude Code Pre-Tool-Use Hook — Installer & Entrypoint
# Installed to ~/.claude/hooks/pre-tool-use/

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK_DIR="$HOME/.claude/hooks"
HOOK_FILE="$HOOK_DIR/pre-tool-use"

install() {
    mkdir -p "$HOOK_DIR"
    
    # Find Python
    PYTHON=""
    for cmd in python3 python python3.12 python3.11; do
        if command -v "$cmd" &>/dev/null; then
            PYTHON="$cmd"
            break
        fi
    done
    
    if [ -z "$PYTHON" ]; then
        echo "❌ Python not found. Install Python 3.10+."
        exit 1
    fi
    
    # Copy the hook script
    cp "$SCRIPT_DIR/block-destructive-commands.py" "$HOOK_DIR/"
    chmod +x "$HOOK_DIR/block-destructive-commands.py"
    
    # Create executable hook (Claude Code expects a single executable file)
    cat > "$HOOK_FILE" << 'HOOKEOF'
#!/usr/bin/env python3
"""Pre-tool-use hook: blocks destructive bash commands."""
import sys, os, json, re
from datetime import datetime

DESTRUCTIVE_PATTERNS = {
    "rm -rf /": "Blocked: `rm -rf /` would destroy the root filesystem",
    "rm -rf /*": "Blocked: Recursive deletion of root is never intentional",
    "git push --force": "Blocked: Use `--force-with-lease` instead",
    "git push -f": "Blocked: Use `--force-with-lease` instead",
    "DROP TABLE": "Blocked: `DROP TABLE` permanently deletes tables",
    "DROP DATABASE": "Blocked: `DROP DATABASE` permanently deletes the database",
    "TRUNCATE": "Blocked: `TRUNCATE` removes all rows irreversibly",
    "mkfs.": "Blocked: Formatting filesystem destroys all data",
    "dd if=/dev/zero": "Blocked: Writing zeros destroys data",
    "shutdown": "Blocked: System shutdown outside code scope",
    "reboot": "Blocked: System reboot outside code scope",
    "chmod -R 777": "Blocked: World-writable permissions are a security risk",
    "iptables -F": "Blocked: Flushing firewall breaks system security",
    "ufw disable": "Blocked: Disabling firewall creates a security hole",
}

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def is_dangerous(cmd):
    cmd_lower = cmd.lower().strip()
    for pattern, message in DESTRUCTIVE_PATTERNS.items():
        if pattern.lower() in cmd_lower:
            return message
    # DELETE FROM without WHERE
    if re.search(r'\bdelete\s+from\b', cmd_lower, re.IGNORECASE):
        m = re.search(r'\bdelete\s+from\b', cmd_lower, re.IGNORECASE)
        if m:
            rest = cmd_lower[m.end():]
            if 'where' not in rest and 'limit' not in rest and 'echo' not in cmd_lower:
                return "Blocked: DELETE FROM without WHERE clause"
    return None

def log_blocked(cmd, reason):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] BLOCKED | {os.getcwd()} | {cmd[:200]} | {reason}\n")

def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({}))
        return
    try:
        tu = json.loads(raw)
        cmd = tu.get("command", "") if isinstance(tu, dict) else ""
        if not cmd:
            print(raw.strip()); return
        reason = is_dangerous(cmd)
        if reason:
            log_blocked(cmd, reason)
            print(json.dumps({}))
            sys.stderr.write(f"\n\u26a0\ufe0f {reason}\n")
        else:
            print(raw.strip())
    except:
        print(raw.strip())

if __name__ == "__main__":
    main()
HOOKEOF
    chmod +x "$HOOK_FILE"
    
    echo "✅ Hook installed to $HOOK_FILE"
    echo "   Blocked attempts logged to $HOOK_DIR/blocked.log"
    echo ""
    echo "Quick test:"
    echo '  echo '\''{"command":"rm -rf /"}'\'' | python3 '"$HOOK_FILE"
}

uninstall() {
    if [ -f "$HOOK_FILE" ]; then
        rm "$HOOK_FILE"
        rm -f "$HOOK_DIR/block-destructive-commands.py"
        echo "✅ Hook uninstalled"
    else
        echo "⚠️  Hook not installed"
    fi
}

test_hook() {
    echo "Testing hook with dangerous commands..."
    echo '{"command":"rm -rf /"}' | python3 "$HOOK_DIR/block-destructive-commands.py" 2>&1 | head -1
    echo '{"command":"git push --force"}' | python3 "$HOOK_DIR/block-destructive-commands.py" 2>&1 | head -1
    echo '{"command":"DROP TABLE users"}' | python3 "$HOOK_DIR/block-destructive-commands.py" 2>&1 | head -1
    echo '{"command":"npm install express"}' | python3 "$HOOK_DIR/block-destructive-commands.py" 2>&1 | head -1
    echo ""
    echo "Blocked log:"
    cat "$HOOK_DIR/blocked.log" 2>/dev/null || echo "(empty)"
}

case "${1:-install}" in
    install) install ;;
    uninstall) uninstall ;;
    test) test_hook ;;
    *) echo "Usage: $0 {install|uninstall|test}" ;;
esac
