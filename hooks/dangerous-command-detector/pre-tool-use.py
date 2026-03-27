#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Dangerous Command Detector

Blocks dangerous bash commands before execution to prevent accidental damage.

Installation (2 commands):
  mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/ljapptest-art/dangerous-hook/main/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
  echo '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/pre-tool-use.py"}]}]}}' > ~/.claude/settings.json
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    {"pattern": r"\brm\s+(-[rf]+\s+|-[a-z]*r[a-z]*\s+|-[a-z]*f[a-z]*\s+).*", "name": "rm -rf", "description": "Recursive force delete can cause irreversible data loss", "severity": "critical"},
    {"pattern": r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", "name": "DROP TABLE/DATABASE", "description": "Dropping tables or databases causes permanent data loss", "severity": "critical"},
    {"pattern": r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z_]", "name": "TRUNCATE", "description": "Truncating tables removes all data without rollback", "severity": "critical"},
    {"pattern": r"\bgit\s+push\s+.*--force\b(?!.*--force-with-lease)", "name": "git push --force", "description": "Force pushing can overwrite remote history", "severity": "critical"},
    {"pattern": r"\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)", "name": "DELETE FROM without WHERE", "description": "Deleting without WHERE clause removes all rows", "severity": "critical"},
    {"pattern": r">\s*/dev/(sd[a-z]|hd[a-z]|nvme[0-9])", "name": "Direct disk write", "description": "Writing directly to disk devices can corrupt filesystems", "severity": "critical"},
    {"pattern": r"\bchmod\s+(-R\s+)?777\b", "name": "chmod 777", "description": "World-writable permissions are a security risk", "severity": "high"},
    {"pattern": r"\bcurl\s+.*\|\s*(sudo\s+)?bash\b", "name": "curl | bash", "description": "Piping remote content to bash is a security risk", "severity": "high"},
    {"pattern": r"\bwget\s+.*\|\s*(sudo\s+)?bash\b", "name": "wget | bash", "description": "Piping remote content to bash is a security risk", "severity": "high"},
    {"pattern": r"\bdd\s+.*of=/dev/(sd[a-z]|hd[a-z]|nvme[0-9])", "name": "dd to disk", "description": "dd to disk devices can destroy data", "severity": "critical"}
]

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_command(command: str, pattern_name: str, description: str, project_path: str = ""):
    """Log blocked command attempt to file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = {"timestamp": timestamp, "command": command, "pattern": pattern_name, "description": description, "project_path": project_path}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def check_command(command: str) -> dict | None:
    """Check if command matches any dangerous pattern."""
    for rule in DANGEROUS_PATTERNS:
        if re.search(rule["pattern"], command, re.IGNORECASE):
            return rule
    return None


def main():
    """Main hook entry point - Claude Code PreToolUse format."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name != "Bash":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)
    
    project_path = input_data.get("cwd", os.getcwd())
    
    matched_rule = check_command(command)
    
    if matched_rule:
        log_blocked_command(command, matched_rule["name"], matched_rule["description"], project_path)
        
        # Claude Code hooks format
        reason = f"BLOCKED by safety hook: {matched_rule['name']}. {matched_rule['description']}. Severity: {matched_rule['severity'].upper()}. This command has been logged to ~/.claude/hooks/blocked.log"
        
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason
            }
        }
        
        print(json.dumps(response))
        sys.exit(0)
    
    # Command is safe, allow it
    sys.exit(0)


if __name__ == "__main__":
    main()
