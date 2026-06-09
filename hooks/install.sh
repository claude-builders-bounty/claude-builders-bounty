#!/bin/bash
# Install Claude Code safety hook
# Usage: curl -sSL <raw_url>/install.sh | bash
set -e

HOOK_DIR="$HOME/.claude/hooks"
HOOK_FILE="$HOOK_DIR/pre_tool_use_hook.py"

mkdir -p "$HOOK_DIR"

cat > "$HOOK_FILE" << 'HOOK_EOF'
#!/usr/bin/env python3
"""Claude Code PreToolUse Hook: Block destructive bash commands."""
import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

BLOCKED_PATTERNS = [
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b", "rm -rf: Recursive forced deletion"),
    (r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*r|-[a-zA-Z]*r[a-zA-Z]*f)\s", "rm -rf: Recursive forced deletion"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE: Destructive SQL operation"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE: Destructive SQL operation"),
    (r"\bTRUNCATE\b", "TRUNCATE: Destructive SQL operation"),
    (r"\bDELETE\s+FROM\b(?![\s\S]*\bWHERE\b)", "DELETE FROM without WHERE: Deletes all rows"),
    (r"\bgit\s+push\b.*--force(?!-with-lease)", "git push --force: Force push overwrites history"),
    (r"\bgit\s+push\b.*-f\b(?![-l])", "git push -f: Force push overwrites history"),
    (r"\bmkfs\b", "mkfs: Formats filesystem"),
    (r"\bdd\s+.*of=/dev/", "dd to device: Can overwrite disks"),
    (r":(){ :\|:& };:", "Fork bomb: Crash system"),
    (r"\bcurl\b.*\|\s*(ba)?sh", "curl pipe to shell: Remote code execution"),
    (r"\bwget\b.*\|\s*(ba)?sh", "wget pipe to shell: Remote code execution"),
    (r"\bchmod\s+-R\s+777\b", "chmod 777 -R: Insecure permissions"),
]

def load_config():
    p = Path.home() / ".claude" / "hooks" / "config.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except: pass
    return {}

def check_command(cmd, config):
    for a in config.get("allow_patterns", []):
        if a in cmd: return None
    for pat, reason in BLOCKED_PATTERNS + [(e, f"Custom: {e}") for e in config.get("extra_patterns", [])]:
        try:
            if re.search(pat, cmd, re.IGNORECASE): return reason
        except re.error:
            if pat.lower() in cmd.lower(): return reason
    return None

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"decision": "allow"})); return
        data = json.loads(raw)
    except:
        print(json.dumps({"decision": "allow"})); return

    if data.get("tool", "") not in ("bash", "Bash", "terminal", "shell"):
        print(json.dumps({"decision": "allow"})); return

    cmd = data.get("input", {}).get("command", "")
    if not cmd:
        print(json.dumps({"decision": "allow"})); return

    config = load_config()
    reason = check_command(cmd, config)

    if reason:
        log_path = Path(config.get("log_file", "~/.claude/hooks/blocked.log")).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with open(log_path, "a") as f:
            f.write(f"[{ts}] BLOCKED\n  Command: {cmd}\n  Reason:  {reason}\n  Project: {os.getcwd()}\n{'─'*60}\n")
        print(json.dumps({"decision": "block", "reason": f"🚫 Blocked: {reason}\nCommand: `{cmd}`\nLogged to {log_path}"}))
    else:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
HOOK_EOF

chmod +x "$HOOK_FILE"
echo "✅ Hook installed at $HOOK_FILE"
echo "   Blocked commands will be logged to $HOOK_DIR/blocked.log"
