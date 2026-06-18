#!/usr/bin/env python3
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

RULES = [
      ("rm -rf", re.compile(r"(^|[;&|]\s*)rm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b")),
      ("rm -rf", re.compile(r"(^|[;&|]\s*)rm\s+-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*\b")),
      ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.I)),
      ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*(--force|-f|--force-with-lease)\b", re.I)),
      ("TRUNCATE", re.compile(r"\btruncate(\s+table)?\b", re.I)),
]

DELETE_FROM = re.compile(r"\bdelete\s+from\s+[\w\".`\[\]-]+(?P<tail>[^;\n]*)", re.I)


def payload():
      raw = sys.stdin.read().strip()
      if not raw:
                return {}
            try:
                      data = json.loads(raw)
                      return data if isinstance(data, dict) else {}
except json.JSONDecodeError:
        return {"command": raw}


def command(data):
      if isinstance(data, str):
                return data
            if not isinstance(data, dict):
                      return ""
                  for key in ("command", "cmd", "input", "tool_input", "toolInput", "parameters", "args", "arguments"):
                            value = data.get(key)
                            found = command(value)
                            if found:
                                          return found
                                  return ""


def blocked(cmd):
      for name, pattern in RULES:
                if pattern.search(cmd):
                              return name
                      for match in DELETE_FROM.finditer(cmd):
                                if not re.search(r"\bwhere\b", match.group("tail") or "", re.I):
                                              return "DELETE FROM without WHERE"
                                      return ""


def project(data):
      for key in ("cwd", "project_path", "projectPath", "workspace", "repo_path"):
                if isinstance(data.get(key), str) and data[key]:
                              return data[key]
    return os.getcwd()


def main():
      data = payload()
    cmd = command(data)
    rule = blocked(cmd)
    if not rule:
              return 0
    LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
              "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
              "command": cmd,
              "project_path": project(data),
              "rule": rule,
    }
    LOG.write_text(LOG.read_text("utf-8") + json.dumps(event) + "\n" if LOG.exists() else json.dumps(event) + "\n", "utf-8")
    print(f"Blocked destructive bash command: {rule}", file=sys.stderr)
    print(f"Attempt logged to: {LOG}", file=sys.stderr)
    return 2


if __name__ == "__main__":
      raise SystemExit(main())
