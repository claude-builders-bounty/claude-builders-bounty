#!/usr/bin/env python3
"""Claude Code PreToolUse hook: blocks destructive bash commands before they run.

Implements the acceptance criteria of claude-builders-bounty issue #3:
  - blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE,
    DELETE FROM without WHERE
  - logs every blocked attempt to ~/.claude/hooks/blocked.log
    (timestamp, attempted command, project path)
  - prints a clear reason to Claude
  - never interferes with normal bash commands

Blocking mechanism (Claude Code hooks convention): on a blocked command
this script prints a JSON decision, writes the reason to stderr, and exits
with code 2. On an allowed command it prints an approve decision and exits 0.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone


def _rm_blocked(segment):
    """True if this single-command segment is rm with recursive+force."""
    m = re.match(r"^(?:sudo\s+)?rm\b(.*)$", segment.strip())
    if not m:
        return False
    rest = m.group(1)
    tokens = rest.split()
    has_r = False
    has_f = False
    for tok in tokens:
        if tok.startswith("--"):
            if tok == "--recursive":
                has_r = True
            elif tok == "--force":
                has_f = True
        elif tok.startswith("-") and len(tok) > 1:
            flags = tok[1:]
            if "r" in flags:
                has_r = True
            if "f" in flags:
                has_f = True
    return has_r and has_f


def find_block_reason(command):
    """Return a human-readable reason if the command must be blocked, else None."""
    segments = re.split(r"[;&|\n]", command)
    for segment in segments:
        seg = segment.strip()
        if not seg:
            continue
        if _rm_blocked(seg):
            return "rm with recursive+force flags (rm -rf)"
        if re.search(r"\bgit\s+push\b.*--force\b", seg):
            return "git push --force"
        if re.search(r"\bgit\s+push\b.*\s-f\b", seg):
            return "git push -f"
        if re.search(r"\bDROP\s+TABLE\b", seg, re.I):
            return "DROP TABLE"
        if re.search(r"\bTRUNCATE\b", seg, re.I):
            return "TRUNCATE"
        if re.search(r"\bDELETE\s+FROM\b", seg, re.I) and not re.search(
            r"\bWHERE\b", seg, re.I
        ):
            return "DELETE FROM without WHERE"
    return None


def log_blocked(command, project_path):
    try:
        log_dir = os.path.expanduser("~/.claude/hooks")
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        with open(os.path.join(log_dir, "blocked.log"), "a") as f:
            f.write(f"{ts} | {project_path} | {command}\n")
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = tool_input.get("command", "") or ""
    project_path = data.get("cwd") or os.getcwd()

    reason = find_block_reason(command) if command else None
    if reason:
        log_blocked(command, project_path)
        msg = f"Blocked destructive command ({reason}): {command}"
        print(json.dumps({"decision": "block", "reason": msg}))
        print(msg, file=sys.stderr)
        return 2
    print(json.dumps({"decision": "approve"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
