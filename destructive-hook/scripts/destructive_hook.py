#!/usr/bin/env python3
"""PreToolUse hook: block destructive bash commands in Claude Code.

Reads a JSON payload on stdin (tool_name + tool_input), inspects the
command, and exits 2 with a warning on stderr when the command is
destructive. Exit code 0 allows the command through.

Every blocked attempt is appended to ~/.claude/hooks/blocked.log with
the timestamp, the attempted command, and the project path (the
`cwd` field from the hook payload). Set DESTRUCTIVE_HOOK_LOG to a
different file to override the log location.

Destructive patterns detected:
  - rm -rf / or rm -rf on broad paths
  - git push --force / + to shared refs
  - git reset --hard / git clean -fdx
  - DROP TABLE / DATABASE / TRUNCATE / DELETE without WHERE
  - > /dev/sd* (raw disk writes)
  - mkfs, dd if= of=/dev/sd*
  - chmod -R 777 /
  - kill -9 on system PIDs
  - sudo rm -rf
"""
import json
import os
import re
import sys
from datetime import datetime

LOG_FILE = os.environ.get(
    "DESTRUCTIVE_HOOK_LOG",
    os.path.expanduser("~/.claude/hooks/blocked.log"),
)


def extract_command(tool_input):
    """Pull the shell command string out of a tool input dict."""
    if not isinstance(tool_input, dict):
        return ""
    for key in ("command", "cmd", "script", "bash", "shell"):
        val = tool_input.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


# (pattern, reason)
DESTRUCTIVE_RULES = [
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-R\s+-f|-f\s+-R)[\s/]+(/|~|\$HOME|\*)(?!\S)", "recursive force remove of a broad path"),
    (r"\bsudo\s+rm\s+-rf", "recursive force remove via sudo"),
    (r"\brm\s+-rf\s+/\s*(;|&&|\||$)", "recursive force remove of root"),
    (r"\bgit\s+push\s+(-f\b|--force\b)(?!-with-lease)", "force push (can overwrite shared history)"),
    (r"\bgit\s+push\s+\+\S", "force push via refspec (can overwrite shared history)"),
    (r"\bgit\s+reset\s+--hard\b", "hard reset (discards working tree changes)"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean with force (removes untracked files)"),
    (r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\b", "SQL DROP"),
    (r"\bTRUNCATE\s+(TABLE\s+)?\w+", "SQL TRUNCATE"),
    (r"\bDELETE\s+FROM\s+\w+(?![^;]*\bWHERE\b)", "SQL DELETE without WHERE (whole statement)"),
    (r">\s*/dev/(sd|nvme|hd|mmcblk|disk)", "raw write to block device"),
    (r"\bmkfs(\.[a-z0-9]+)?\b", "filesystem format"),
    (r"\bdd\b[^;|&]*\bof=/dev/", "dd writing to a block device"),
    (r"\bchmod\s+-R\s+777\s+/\s*(;|&&|\||$)", "recursive world-writable on root"),
    (r"\bkill\s+(-9|--signal=9|-KILL)\s+(1|2|3|4)\b", "kill system-critical PID"),
    (r"\bshred\s+", "secure delete"),
    (r"\bwipefs\b", "wipe filesystem signatures"),
]

COMPILED = [(re.compile(p), reason) for p, reason in DESTRUCTIVE_RULES]


def log_blocked(reason, cmd, project):
    """Append one line to the blocked-commands log. Never raises."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        ts = datetime.now().astimezone().isoformat(timespec="seconds")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"{ts} | reason={reason} | project={project} | "
                f"command={cmd.replace(chr(10), ' ')!r}\n"
            )
    except Exception:
        pass  # logging must never change the block decision


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Not a hook invocation; allow through.
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    project = payload.get("cwd") or os.getcwd()

    # Only inspect shell-type tools.
    if tool_name not in ("Bash", "bash", "shell", "exec", "execute_command"):
        sys.exit(0)

    cmd = extract_command(tool_input)
    if not cmd:
        sys.exit(0)

    for pattern, reason in COMPILED:
        if pattern.search(cmd):
            log_blocked(reason, cmd, project)
            print(
                f"[destructive-hook] BLOCKED: this command was not run.\n"
                f"  reason: {reason}\n"
                f"  command: {cmd}\n"
                f"  logged to: {LOG_FILE}\n"
                f"Do not retry this command. If the operation is genuinely "
                f"needed, ask the user to run it manually outside Claude Code.",
                file=sys.stderr,
            )
            sys.exit(2)  # exit 2 = deny, stderr is fed back to the model

    sys.exit(0)  # allow


if __name__ == "__main__":
    main()
