#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive bash commands."""
import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

RULES = [
    ("rm -rf", re.compile(r"(?i)(^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-?[A-Za-z]*f[A-Za-z]*r)[\s=~/]")),
    ("DROP TABLE", re.compile(r"(?is)\bdrop\s+table\b")),
    ("git push --force", re.compile(r"(?i)\bgit\s+push\b[^\n;|&]*\s--force(?:\s|=|$)|\bgit\s+push\b[^\n;|&]*\s-f(?:\s|$)")),
    ("TRUNCATE", re.compile(r"(?is)\btruncate\b")),
    ("DELETE FROM without WHERE", re.compile(r"(?is)\bdelete\s+from\b(?:(?!\bwhere\b|;).)*(?:;|$)")),
]

def extract_command(payload):
    tool = payload.get("tool_input") or payload.get("input") or payload
    if isinstance(tool, dict):
        return str(tool.get("command") or tool.get("cmd") or tool.get("bash") or "")
    return ""

def log_block(command, project, rule):
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    safe = command.replace("\n", "\\n")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\trule={rule}\tproject={project}\tcommand={safe}\n")

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    command = extract_command(payload)
    project = payload.get("cwd") or payload.get("project_dir") or os.getcwd()
    for name, pattern in RULES:
        if pattern.search(command):
            log_block(command, project, name)
            print(f"Blocked dangerous bash command: {name}. Request explicit human approval or use a safer, reversible alternative.", file=sys.stderr)
            return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
