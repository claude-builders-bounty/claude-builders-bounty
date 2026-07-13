#!/usr/bin/env python3
"""
Pre-tool-use safety hook for Claude Code.

Blocks destructive bash commands before they execute:
  - `rm -rf` / `rm -r -f` (recursive force delete)
  - `git push --force` / `-f` / `--force-with-lease`
  - `DROP TABLE`
  - `TRUNCATE`
  - `DELETE FROM` without a `WHERE` clause

Every blocked attempt is logged to ~/.claude/hooks/blocked.log with:
timestamp | attempted command | project path | reason

Register in ~/.claude/settings.json:
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/block_destructive.py" }
        ]
      }
    ]
  }
}

Claude Code blocks the tool call when this hook exits non-zero and shows the
message on stderr. (Also emits the JSON decision for newer hook runtimes.)
"""
import sys, json, os, re

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")
PROJECT_HINT = os.environ.get("PWD", "unknown")

# (label, regex)
PATTERNS = [
    ("rm -rf", re.compile(r"\brm\s+(-[^\s]*\s+)*(-r|--recursive)\b.*\bf\b|\brm\s+(-[^\s]*\s+)*(-f|--force)\b.*\br\b|\brm\s+-rf\b|\brm\s+-fr\b", re.I)),
    ("git push --force", re.compile(r"\bgit\s+push\b(?!.*--no-force)(.*(--force|-\w*f\w*|force-with-lease))", re.I)),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.I)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\b", re.I)),
]


def log_and_block(reason: str, command: str) -> int:
    ts = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(f"{ts} | cmd={command!r} | project={PROJECT_HINT} | reason={reason}\n")
    except Exception:
        pass
    msg = f"🛑 Blocked by safety hook: {reason}. Command was NOT executed."
    sys.stdout.write(json.dumps({"decision": "block", "reason": msg}) + "\n")
    sys.stderr.write(msg + "\n")
    return 2


def scan(command: str) -> int:
    if not command:
        return 0
    if re.search(r"\bDELETE\s+FROM\b", command, re.I) and not re.search(r"\bWHERE\b", command, re.I):
        return log_and_block("DELETE FROM without a WHERE clause", command)
    for label, pat in PATTERNS:
        if pat.search(command):
            return log_and_block(label, command)
    return 0


def main() -> int:
    raw = ""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except Exception:
        # Non-JSON input (e.g. raw command line piped in): scan it directly.
        return scan(raw.strip() or os.environ.get("CMD", ""))
    if data.get("tool_name", "") != "Bash":
        return 0
    command = (data.get("tool_input", {}) or {}).get("command", "") or ""
    return scan(command)


if __name__ == "__main__":
    sys.exit(main())
