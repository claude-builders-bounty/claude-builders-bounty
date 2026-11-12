#!/usr/bin/env python3
"""
pre-tool-use hook for Claude Code — blocks destructive bash commands.

Reads the PreToolUse hook payload from stdin (JSON), inspects the Bash command,
and denies execution when it matches a dangerous pattern. Logs every block.

Install:
  mkdir -p ~/.claude/hooks
  cp pre_tool_use_block.sh ~/.claude/hooks/
  chmod +x ~/.claude/hooks/pre_tool_use_block.sh
Then add to ~/.claude/settings.json:
  {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "~/.claude/hooks/pre_tool_use_block.sh"}]}]}}
"""
import json, sys, re, os
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# Dangerous patterns: (regex, human-readable reason)
DANGEROUS = [
    (re.compile(r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b", re.IGNORECASE), "recursive force delete (rm -rf)"),
    (re.compile(r"\bdrop\s+table\b", re.IGNORECASE), "DROP TABLE (destroys data)"),
    (re.compile(r"\btruncate\s+(table\s+)?", re.IGNORECASE), "TRUNCATE TABLE (destroys all rows)"),
    (re.compile(r"\bgit\s+push\s+(-[a-z]*\s+)*--force", re.IGNORECASE), "force push (rewrites history)"),
    (re.compile(r"\bgit\s+push\s+.*\+\w+:", re.IGNORECASE), "force push (force-push refspec)"),
]

def _is_delete_without_where(command):
    """Block DELETE FROM only when no WHERE clause is present anywhere in the command."""
    if not re.search(r"\bdelete\s+from\b", command, re.IGNORECASE):
        return False
    return not re.search(r"\bwhere\b", command, re.IGNORECASE)

def log_block(command, project, reason):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts} | project={project or 'unknown'} | reason={reason} | command={command}\n"
    with open(LOG_PATH, "a") as f:
        f.write(line)

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Not valid JSON — allow (do not interfere)
        sys.exit(0)

    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""

    # Only inspect Bash commands; ignore everything else (non-interference)
    if not command:
        sys.exit(0)

    # Special case: DELETE FROM without WHERE (needs the full-command check)
    if _is_delete_without_where(command):
        log_block(command, payload.get("cwd", ""), "DELETE FROM without WHERE (wipes table)")
        deny = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Blocked destructive command: DELETE FROM without a WHERE clause. "
                    "This would wipe the entire table. Add a WHERE clause if intentional."
                ),
            }
        }
        print(json.dumps(deny))
        sys.exit(2)

    for pattern, reason in DANGEROUS:
        if pattern.search(command):
            log_block(command, payload.get("cwd", ""), reason)
            deny = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Blocked destructive command: {reason}. "
                        "This pattern can cause irreversible data loss. "
                        "If this is intentional, review the exact command and confirm."
                    ),
                }
            }
            print(json.dumps(deny))
            sys.exit(2)  # exit code 2 = block the tool call

    # Command is safe — allow
    sys.exit(0)

if __name__ == "__main__":
    main()
