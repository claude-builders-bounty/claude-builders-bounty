#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code: block destructive bash commands before they run.

Install (2 commands):
  1. mkdir -p ~/.claude/hooks && cp block-destructive-bash.py ~/.claude/hooks/
  2. Register the PreToolUse Bash matcher in ~/.claude/settings.json:

     {
       "hooks": {
         "PreToolUse": [
           {
             "matcher": "Bash",
             "hooks": [
               { "type": "command", "command": "python3 ~/.claude/hooks/block-destructive-bash.py" }
             ]
           }
         ]
       }
     }

Blocked patterns:
  - rm -rf (also rm -fr, rm -r -f, rm --recursive --force)
  - DROP TABLE
  - git push --force (also git push -f)
  - TRUNCATE [TABLE]
  - DELETE FROM without a WHERE clause

Every blocked attempt is appended to ~/.claude/hooks/blocked.log with a
timestamp, the attempted command, and the project path (cwd).
Normal, non-destructive bash commands are left untouched (exit 0, no decision).
"""

import datetime
import json
import os
import pathlib
import re
import sys

HOME = os.path.expanduser("~")
HOOK_DIR = os.path.join(HOME, ".claude", "hooks")
LOG_FILE = os.path.join(HOOK_DIR, "blocked.log")


def classify(command: str):
    """Return the matched rule name, or None if the command is safe."""
    cl = command.lower()

    # rm -rf / rm -fr / rm -r -f / rm --recursive --force
    rm = re.search(r"\brm\b([^;|&]*)", cl)
    if rm:
        seg = rm.group(1)
        has_rec = bool(
            re.search(r"(^|\s)-[a-z]*r[a-z]*\b", seg) or "--recursive" in seg
        )
        has_for = bool(
            re.search(r"(^|\s)-[a-z]*f[a-z]*\b", seg) or "--force" in seg
        )
        if has_rec and has_for:
            return "rm -rf (recursive force delete)"

    if re.search(r"\bdrop\s+table\b", cl):
        return "DROP TABLE"

    if re.search(r"\bgit\s+push\b", cl) and (
        re.search(r"--force\b", cl) or re.search(r"\B-f\b", cl)
    ):
        return "git push --force"

    if re.search(r"\btruncate\b", cl):
        return "TRUNCATE"

    # DELETE FROM without WHERE, checked per statement (split on ';')
    for stmt in cl.split(";"):
        if re.search(r"\bdelete\s+from\b", stmt) and not re.search(r"\bwhere\b", stmt):
            return "DELETE FROM without WHERE"

    return None


def log_blocked(command: str, cwd: str, rule: str) -> None:
    try:
        pathlib.Path(HOOK_DIR).mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        line = f"[{ts}] cwd={cwd} rule={rule} command={command}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        # Never let logging break the hook's denial decision.
        pass


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        # Malformed input: do not interfere with the normal flow.
        sys.exit(0)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = (data.get("tool_input") or {}).get("command", "")
    cwd = data.get("cwd", "")
    if not command:
        sys.exit(0)

    rule = classify(command)
    if rule is None:
        sys.exit(0)

    log_blocked(command, cwd, rule)

    reason = (
        f"Blocked by safety hook: '{rule}' is a destructive command and is not "
        "allowed here. Remove the destructive flag or rewrite the command safely; "
        "if the operation is genuinely required, ask the user for explicit approval. "
        "The attempt has been logged to ~/.claude/hooks/blocked.log."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
