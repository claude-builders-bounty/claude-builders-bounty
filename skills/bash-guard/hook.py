#!/usr/bin/env python3
"""
bash-guard.py — PreToolUse hook for Claude Code.
Blocks destructive bash commands. Logs all blocked attempts.

Installation:
  1. Copy this file to your project's .claude/hooks/ directory
  2. Add to .claude/settings.json (see README.md)

Behaviour:
  - Blocks: rm -rf, DROP TABLE, TRUNCATE, DELETE FROM without WHERE,
            git push --force / -f, dd if=/dev/sda
  - Logs every blocked attempt to ~/.claude/hooks/blocked.log
  - Lets safe commands pass through unchanged
"""

import json
import os
import re
import sys
from datetime import datetime


LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def log_blocked(command, reason, cwd):
    """Append a blocked command entry to the log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  Command: {command}\n"
        f"  Reason:  {reason}\n"
        f"  Project: {cwd}\n"
        f"  {'=' * 50}\n"
    )
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass  # Silently ignore if we cannot write to the log


def should_block(cmd):
    """
    Return (True, reason) if the command should be blocked,
    or (False, None) if it is safe.
    """
    cmd_lower = cmd.lower().strip()

    # --- rm -rf ---
    # Match: rm -rf, rm -fr, rm -r -f, rm --recursive --force, sudo rm -rf, etc.
    cleaned = cmd_lower
    for prefix in ["sudo ", "\\"]:
        cleaned = cleaned.replace(prefix, "")
    cleaned = cleaned.strip()
    if cleaned.startswith("rm "):
        args_str = cleaned[3:].strip()  # Everything after 'rm '
        has_r = bool(re.search(r'(?:^|\s)-{1,2}r(?:ecursive)?(?:\s|$)', args_str))
        has_f = bool(re.search(r'(?:^|\s)-{1,2}f(?:orce)?(?:\s|$)', args_str))
        # Also check combined flags like -rf, -fr
        has_combined = bool(re.search(r'(?:^|\s)-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*', args_str)) or \
                       bool(re.search(r'(?:^|\s)-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*', args_str))
        if (has_r and has_f) or has_combined:
            return True, "rm -rf is blocked: recursive force delete is destructive and irreversible"

    # --- DROP TABLE ---
    if re.search(r"\bdrop\s+table\b", cmd_lower):
        return True, "DROP TABLE is blocked: this would destroy a database table and all its data"

    # --- TRUNCATE ---
    if re.search(r"\btruncate\b", cmd_lower):
        return True, "TRUNCATE is blocked: this would wipe all rows from a database table"

    # --- DELETE FROM without WHERE or LIMIT ---
    del_match = re.search(r"\bdelete\s+from\b", cmd_lower)
    if del_match:
        has_where = re.search(r"\bwhere\b", cmd_lower)
        has_limit = re.search(r"\blimit\b", cmd_lower)
        if not has_where and not has_limit:
            return True, "DELETE FROM without WHERE is blocked: this would delete all rows from the table"

    # --- git push --force / -f ---
    if "git" in cmd_lower and "push" in cmd_lower:
        cleaned_push = cmd_lower.replace("sudo ", "").strip()
        if " --force" in cleaned_push or " -f " in cleaned_push or cleaned_push.endswith(" -f"):
            return True, "git push --force is blocked: force push can destroy remote history for other contributors"

    # --- dd dangerous writes ---
    if "dd " in cmd_lower and ("if=" in cmd_lower or "if =" in cmd_lower):
        if re.search(r"of=\s*/dev/", cmd_lower):
            return True, "dd write to /dev/ device is blocked: this can corrupt your disk or partition"

    return False, None


def main():
    raw = sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Failed to parse hook input: {e}", file=sys.stderr)
        sys.exit(2)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    cwd = data.get("cwd", os.getcwd())

    # Only process Bash tool calls
    if tool_name != "Bash":
        # Allow all non-Bash tools
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow"
            }
        }))
        sys.exit(0)

    command = tool_input.get("command", "")

    block, reason = should_block(command)

    if block:
        log_blocked(command, reason, cwd)
        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason
            }
        }
        print(json.dumps(result))
        sys.exit(0)

    # Safe command — let it through
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }
    }))


if __name__ == "__main__":
    main()
