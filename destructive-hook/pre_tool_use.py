#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks dangerous bash commands.
Place at: ~/.claude/hooks/pre_tool_use.py
"""

import sys, json, os, re
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS_PATTERNS = [
    # Destructive filesystem operations
    (r'rm\s+-rf\s+[/~]', "rm -rf on root/home — irreversible deletion"),
    (r'rm\s+-rf\s+\*', "rm -rf * — mass deletion"),
    (r'rm\s+-rf\s+\.\.?(\/|\\)', "rm -rf parent directory"),
    (r'rm\s+-rf\s+/(usr|etc|var|opt|bin|sbin|lib|boot|dev|proc|sys)\b', "rm -rf system directory"),
    (r'>\s*/dev/sd[a-z]', "Writing directly to block device"),

    # Destructive database operations
    (r'\bDROP\s+TABLE\b', "DROP TABLE — irreversible data loss"),
    (r'\bDROP\s+DATABASE\b', "DROP DATABASE — complete database destruction"),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', "TRUNCATE — removes all rows"),
    (r'\bDELETE\s+FROM\s+\w+\s*(?!WHERE)', "DELETE FROM without WHERE clause — mass data deletion"),
    (r'\bDELETE\s+FROM\s+\w+\s*;', "DELETE FROM without WHERE clause"),

    # Dangerous git operations
    (r'git\s+push\s+--force\b(?!.*--lease)', "git push --force without --lease — overwrites remote history"),
    (r'git\s+push\s+-f\b(?!.*--lease)', "git push -f without --lease"),
    (r'git\s+reset\s+--hard\b', "git reset --hard — discards uncommitted changes"),
    (r'git\s+clean\s+-[fidx]+', "git clean — removes untracked files"),

    # Shell/system dangers
    (r'chmod\s+777\s+[/~]', "chmod 777 on root/home — security risk"),
    (r'chmod\s+-R\s+777\b', "chmod -R 777 — recursive world-writable permissions"),
    (r'curl\s+.*\|\s*(ba)?sh\b', "curl pipe to shell — potential RCE"),
    (r'wget\s+.*\s*-O\s*-\s*\|\s*(ba)?sh\b', "wget pipe to shell — potential RCE"),
    (r':(){ :|:& };:', "Fork bomb detected"),
    (r'\bdd\s+if=.*of=/dev/', "dd writing to device"),
]


def log_block(attempted_command, project_path):
    """Log blocked attempt to file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] BLOCKED | project={project_path} | command={attempted_command}\n")


def check_command(command_str):
    """Returns (blocked: bool, reason: str)."""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command_str, re.IGNORECASE):
            return True, reason
    return False, ""


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "proceed"}))
        return

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only intercept bash/shell commands
    if tool_name not in ("bash", "shell_command", "Bash"):
        print(json.dumps({"decision": "proceed"}))
        return

    command = tool_input.get("command", "")
    project_path = os.getcwd()

    if not command:
        print(json.dumps({"decision": "proceed"}))
        return

    blocked, reason = check_command(command)

    if blocked:
        log_block(command, project_path)
        result = {
            "decision": "block",
            "reason": f"⚠️  BLOCKED: {reason}\n\n"
                      f"Command: `{command[:120]}`\n"
                      f"This command matches a dangerous pattern and was blocked for safety.\n"
                      f"Block logged to: {LOG_FILE}\n\n"
                      f"If you're sure this is safe, use a safer alternative:\n"
                      f"- Instead of `rm -rf /path`, use `mv /path /tmp/to_delete` first\n"
                      f"- Instead of `git push --force`, use `git push --force-with-lease`\n"
                      f"- For DROP/TRUNCATE/DELETE, add appropriate safeguards first"
        }
        print(json.dumps(result))
    else:
        print(json.dumps({"decision": "proceed"}))


if __name__ == "__main__":
    main()
