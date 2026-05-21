#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: Blocks destructive bash commands before execution.

Place this file at: ~/.claude/hooks/pre-tool-use/block_destructive.py
Make it executable: chmod +x block_destructive.py

Configuration in ~/.claude/hooks/config.json:
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use/block_destructive.py"
          }
        ]
      }
    ]
  }
}
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that are always blocked
BLOCKED_PATTERNS = [
    # rm -rf variations
    (r'\brm\s+(?:-[a-z]*r[a-z]*f[a-z]*\s+|-[a-z]*f[a-z]*r[a-z]*\s+|--recursive\s+--force\s+|--force\s+--recursive\s+)', 
     "rm -rf (recursive force remove)"),
    (r'\brm\s+-rf\b', "rm -rf"),
    (r'\brm\s+-fr\b', "rm -fr"),
    (r'\brm\s+--recursive\b', "rm --recursive (add --no-preserve-root or use trash instead)"),
    
    # SQL destructive operations
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW)\b', "DROP TABLE/DATABASE (destructive SQL)"),
    (r'\bTRUNCATE\s+(TABLE\s+)?', "TRUNCATE (destructive SQL)"),
    (r'\bDELETE\s+FROM\s+\w+(?!\s+WHERE\b)', "DELETE FROM without WHERE clause"),
    
    # Git destructive operations
    (r'\bgit\s+push\s+(?:--force|-[a-z]*f[a-z]*)\b', "git push --force (rewrites remote history)"),
    (r'\bgit\s+reset\s+--hard\b', "git reset --hard (discards uncommitted changes)"),
    (r'\bgit\s+clean\s+(?:-[a-z]*[dD][a-z]*f[a-z]*|--force)\b', "git clean -fd (removes untracked files)"),
    
    # Filesystem destruction
    (r'\bdd\s+if=', "dd (can overwrite disks — add of=/dev/null to use safely)"),
    (r'\bmkfs\.', "mkfs (formats filesystems)"),
    (r'\b>:?\s*/dev/sd[a-z]', "redirect to block device (can overwrite disks)"),
    
    # Dangerous chmod/chown
    (r'\bchmod\s+(?:-R\s+)?777\b', "chmod 777 (world-writable permissions)"),
    (r'\bchown\s+(?:-R\s+)?[^:\s]+:[^:\s]+\s+/', "chown on root-level paths"),
    
    # Dangerous network
    (r'\b(?:curl|wget)\s+.*\|\s*(?:ba)?sh\b', "curl/wget piping to shell"),
    (r'\b(?:curl|wget)\s+.*\|\s*(?:sudo\s+)?(?:ba)?sh\b', "curl/wget piping to shell with sudo"),
]

# Patterns that trigger a warning but are not blocked
WARNING_PATTERNS = [
    (r'\bsudo\s+rm\b', "Consider using 'trash' or 'gio trash' instead"),
    (r'\bkill\s+-9\b', "SIGKILL (-9) doesn't allow cleanup; try -15 (SIGTERM) first"),
    (r'\bshutdown\b', "Shutdown will affect all users on this system"),
    (r'\breboot\b', "Reboot will affect all users on this system"),
]


def log_blocked(project_path: str, command: str, reason: str) -> None:
    """Log blocked command to the blocked.log file."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "command": command,
        "reason": reason,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(command: str, project_path: str) -> dict:
    """Check a command against blocked and warning patterns.
    
    Returns:
        dict with keys: blocked (bool), reason (str | None), warnings (list[str])
    """
    result = {"blocked": False, "reason": None, "warnings": []}
    
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            result["blocked"] = True
            result["reason"] = reason
            break
    
    if not result["blocked"]:
        for pattern, warning in WARNING_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                result["warnings"].append(warning)
    
    return result


def main():
    """Main entry point for Claude Code hook."""
    try:
        # Claude Code passes tool input as JSON on stdin
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # Fallback: try reading command-line arguments
        if len(sys.argv) > 1:
            command = " ".join(sys.argv[1:])
            project_path = os.getcwd()
        else:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "pre-tool-use",
                    "permissionDecision": "allow"
                }
            }))
            sys.exit(0)
    else:
        # Extract command from Claude Code's tool input format
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        if tool_name.lower() != "bash":
            # Not a bash command, allow it
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "pre-tool-use",
                    "permissionDecision": "allow"
                }
            }))
            sys.exit(0)
        
        command = tool_input.get("command", "")
        project_path = input_data.get("cwd", os.getcwd())
    
    if not command:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "pre-tool-use",
                "permissionDecision": "allow"
            }
        }))
        sys.exit(0)
    
    result = check_command(command, project_path)
    
    if result["blocked"]:
        log_blocked(project_path, command, result["reason"])
        
        message = (
            f"🚫 BLOCKED: {result['reason']}\n\n"
            f"Command: {command}\n"
            f"Project: {project_path}\n\n"
            f"If you're absolutely sure this is safe, you can:\n"
            f"1. Review the full command manually\n"
            f"2. Run it directly in a terminal outside Claude Code\n"
            f"3. Consider safer alternatives (e.g., 'gio trash' instead of 'rm -rf')\n"
            f"\nThis attempt has been logged to: {LOG_PATH}"
        )
        
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "pre-tool-use",
                "permissionDecision": "deny",
                "permissionDecisionReason": message
            }
        }))
        sys.exit(2)
    
    # Check warnings
    if result["warnings"]:
        warnings_text = "\n".join(f"⚠️  {w}" for w in result["warnings"])
        message = (
            f"⚠️  WARNING — Please review before executing:\n\n"
            f"{warnings_text}\n\n"
            f"Command: {command}\n"
            f"Project: {project_path}"
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "pre-tool-use",
                "permissionDecision": "ask",
                "permissionDecisionReason": message
            }
        }))
        sys.exit(0)
    
    # Allow the command
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "pre-tool-use",
            "permissionDecision": "allow"
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
