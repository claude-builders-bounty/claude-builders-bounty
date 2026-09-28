#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive shell commands."""
from __future__ import annotations
import os, re, sys, time
from pathlib import Path

CMD = " ".join(sys.argv[1:]) or os.environ.get("CLAUDE_TOOL_INPUT", "")
ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "genie-bounty-delivery" / "blocked.log"
LOG.parent.mkdir(parents=True, exist_ok=True)
low = CMD.lower()
rules = [
    (r"(^|\s)rm\s+(-[a-z]*f[a-z]*|--force).*|rm\s+-rf", "Blocked destructive command: rm -rf (refusing to delete recursively)."),
    (r"drop\s+table", "Blocked destructive SQL: DROP TABLE."),
    (r"git\s+push\s+.*--force|git\s+push\s+-f\b", "Blocked dangerous git: push --force."),
    (r"truncate\s+table", "Blocked destructive SQL: TRUNCATE."),
]
msg = ""
for pat, m in rules:
    if re.search(pat, low):
        msg = m
        break
if not msg and re.search(r"delete\s+from\s+[\w.]+", low) and "where" not in low:
    msg = "Blocked destructive SQL: DELETE FROM without WHERE."
if msg:
    LOG.open("a", encoding="utf-8").write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} BLOCKED: {CMD} :: {msg}\n")
    print(msg, file=sys.stderr)
    raise SystemExit(2)
raise SystemExit(0)
