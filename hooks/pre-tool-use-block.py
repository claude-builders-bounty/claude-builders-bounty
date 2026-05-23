#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_input():
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {"_raw": raw}


def extract_command(payload):
    # Claude Code commonly sends tool metadata in these shapes.
    candidates = [
        payload.get("tool_input", {}).get("command"),
        payload.get("input", {}).get("command"),
        payload.get("params", {}).get("command"),
        payload.get("command"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c
    return ""


def extract_tool_name(payload):
    for k in ("tool_name", "tool", "name"):
        v = payload.get(k)
        if isinstance(v, str):
            return v
    return ""


def extract_project_path(payload):
    # Best-effort path extraction for logging.
    for key in ("cwd", "working_directory", "project_path"):
        v = payload.get(key)
        if isinstance(v, str) and v:
            return v
    for parent in ("session", "context", "tool_input", "input"):
        obj = payload.get(parent)
        if isinstance(obj, dict):
            for key in ("cwd", "working_directory", "project_path"):
                v = obj.get(key)
                if isinstance(v, str) and v:
                    return v
    return os.getcwd()


def is_delete_without_where(cmd):
    s = " ".join(cmd.strip().split())
    # Match a DELETE FROM ... statement lacking WHERE before ';' (or EOL).
    if not re.search(r"\bdelete\s+from\b", s, re.IGNORECASE):
        return False
    m = re.search(r"\bdelete\s+from\b(?P<body>.*?)(;|$)", s, re.IGNORECASE)
    if not m:
        return False
    body = m.group("body")
    return re.search(r"\bwhere\b", body, re.IGNORECASE) is None


def check_block_reason(cmd):
    checks = [
        (re.search(r"(^|\s)rm\s+-rf(\s|$)", cmd), "Blocked dangerous command: rm -rf"),
        (re.search(r"\bdrop\s+table\b", cmd, re.IGNORECASE), "Blocked dangerous SQL: DROP TABLE"),
        (re.search(r"\btruncate\b", cmd, re.IGNORECASE), "Blocked dangerous SQL: TRUNCATE"),
        (re.search(r"\bgit\s+push\s+--force(\s|$)", cmd), "Blocked dangerous git operation: git push --force"),
    ]
    for matched, reason in checks:
        if matched:
            return reason
    if is_delete_without_where(cmd):
        return "Blocked dangerous SQL: DELETE FROM without WHERE clause"
    return ""


def log_block(cmd, project_path):
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_path = hooks_dir / "blocked.log"
    ts = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{project_path}\t{cmd}\n")


def main():
    payload = load_input()
    tool = extract_tool_name(payload).lower()
    cmd = extract_command(payload)

    # Only inspect bash-like tool calls. If metadata absent, still inspect command if present.
    if tool and "bash" not in tool:
        sys.exit(0)
    if not cmd:
        sys.exit(0)

    reason = check_block_reason(cmd)
    if not reason:
        sys.exit(0)

    project_path = extract_project_path(payload)
    log_block(cmd, project_path)

    print(reason, file=sys.stderr)
    print("Reason: policy blocks destructive commands in pre-tool-use hook.", file=sys.stderr)
    print("If intentional, run with explicit human review and safer alternative.", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
