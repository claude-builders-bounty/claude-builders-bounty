#!/usr/bin/env python3
import sys
import os
import json
import re
from datetime import datetime

# Path to log file
LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

# Patterns to block
BLOCKED_PATTERNS = [
    (r'\brm\s+-rf\b', "rm -rf (Destructive file deletion)"),
    (r'\bdrop\s+table\b', "DROP TABLE (Database schema destruction)"),
    (r'\bgit\s+push\s+(?:-[A-Za-z]*f\w*|--force)\b', "git push --force (Overwriting remote git history)"),
    (r'\btruncate\b', "TRUNCATE (Emptying database table)"),
]

# Special check for DELETE FROM without WHERE
def has_delete_without_where(text):
    text_clean = re.sub(r'\s+', ' ', text.lower())
    # Match "delete from table" but ensure "where" does NOT follow
    if "delete from" in text_clean:
        # If there is "delete from", check if "where" is present
        if "where" not in text_clean:
            return True
    return False

def check_text(text):
    # Check simple patterns
    for pattern, desc in BLOCKED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return desc
            
    # Check delete without where
    if has_delete_without_where(text):
        return "DELETE FROM without WHERE clause (Mass database deletion)"
        
    return None

def extract_commands(data):
    """Recursively search for potential command strings in JSON input."""
    commands = []
    if isinstance(data, dict):
        # Check known keys for Claude Code tool invocation
        # e.g. {"tool": "bash", "arguments": {"command": "..."}}
        for key in ['command', 'cmd', 'code', 'script', 'input', 'arguments']:
            if key in data:
                val = data[key]
                if isinstance(val, str):
                    commands.append(val)
                elif isinstance(val, dict) or isinstance(val, list):
                    commands.extend(extract_commands(val))
        # General backup search
        for k, v in data.items():
            if k not in ['command', 'cmd', 'code', 'script', 'input', 'arguments']:
                commands.extend(extract_commands(v))
    elif isinstance(data, list):
        for item in data:
            commands.extend(extract_commands(item))
    return commands

def log_blocked(command, reason, project_path):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "attempted_command": command,
            "blocked_reason": reason,
            "project_path": project_path
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[Warning] Failed to write to blocked log: {e}", file=sys.stderr)

def main():
    project_path = os.getcwd()
    raw_input = ""
    
    # Read stdin (Claude Code hook inputs are passed via stdin)
    if not sys.stdin.isatty():
        raw_input = sys.stdin.read()

    # Fallback to sys.argv if stdin is empty
    if not raw_input.strip() and len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])

    if not raw_input.strip():
        # Nothing to check, allow
        sys.exit(0)

    # 1. Try to parse as JSON first (Claude Code hook protocol)
    commands_to_check = []
    is_json = False
    try:
        data = json.loads(raw_input)
        is_json = True
        commands_to_check = extract_commands(data)
        # If no commands found inside JSON structure, check raw JSON representation
        if not commands_to_check:
            commands_to_check = [raw_input]
    except json.JSONDecodeError:
        # Not JSON, treat raw stdin/arguments as command string
        commands_to_check = [raw_input]

    # 2. Check each target command
    for cmd in commands_to_check:
        reason = check_text(cmd)
        if reason:
            # Command blocked!
            log_blocked(cmd.strip(), reason, project_path)
            
            # Print a clear user-facing warning
            print("\n" + "="*80, file=sys.stderr)
            print(f"🛑 SECURITY CHECK FAILED: Dangerous command blocked!", file=sys.stderr)
            print(f"Reason: {reason}", file=sys.stderr)
            print(f"Command attempted: {cmd.strip()}", file=sys.stderr)
            print(f"Project: {project_path}", file=sys.stderr)
            print(f"Log written to: {LOG_FILE}", file=sys.stderr)
            print("="*80 + "\n", file=sys.stderr)
            
            # Non-zero exit code blocks the tool usage
            sys.exit(1)

    # Safe to execute
    sys.exit(0)

if __name__ == "__main__":
    main()
