#!/usr/bin/env python3
"""pre-tool-use hook - blocks destructive bash commands."""
import json, os, sys
from datetime import datetime
from pathlib import Path

BLOCKED_PATTERNS = [
    lambda c: "rm" in c and "-rf" in c,
    lambda c: "DROP TABLE" in c.upper(),
    lambda c: "TRUNCATE" in c.upper(),
    lambda c: "git push" in c and ("--force" in c or "-f" in c),
    lambda c: "DELETE FROM" in c.upper() and "WHERE" not in c.upper().split("DELETE FROM")[-1][:100],
]

LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

def main():
    payload = json.loads(sys.stdin.read())
    tool_name = payload.get("tool", {}).get("name", "")
    tool_input = payload.get("tool", {}).get("input", {})

    if tool_name != "Bash":
        json.dump({"result": {"effect": "allow"}}, sys.stdout)
        return

    cmd = tool_input.get("command", "")
    allowed = not any(check(cmd) for check in BLOCKED_PATTERNS)

    if not allowed:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a") as f:
            now = datetime.now().isoformat()
            cwd = os.getcwd()
            f.write(f"[{now}] BLOCKED: {cmd}\n")
            f.write(f"  Project: {cwd}\n\n")
        msg = (
            "This command was blocked because it could be destructive.\n"
            + "Use a safer alternative or break it into smaller steps.\n"
            + "If needed, re-run with CONFIRM=1 prefix.\n"
        )
        json.dump({"result": {"effect": "block", "message": msg}}, sys.stdout)
    else:
        json.dump({"result": {"effect": "allow"}}, sys.stdout)

if __name__ == "__main__":
    main()
