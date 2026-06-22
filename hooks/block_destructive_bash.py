#!/usr/bin/env python3
"""Pre-tool-use hook blocking destructive bash commands (Python version)."""
import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

PATTERNS = [
    ("rm-rf-root", r"rm\s+[-\/]*rf?\s*/", "rm -rf targeting root filesystem"),
    ("rm-rf-etc", r"rm\s+[-\/]*rf?\s+/etc", "rm -rf targeting /etc"),
    ("drop-table", r"DROP\s+TABLE", "Destructive DDL - write migration"),
    ("truncate", r"TRUNCATE\s+", "Destructive DDL - write migration"),
    ("git-force-push", r"git\s+push\s+.*\-{1,2}f(?:orce)?\s*$", "Force push rewrites history"),
    ("delete-no-where", r"DELETE\s+FROM\s+\w+\s*$", "DELETE without WHERE"),
    ("update-no-where", r"UPDATE\s+\w+\s+SET\s+.*?(?:\s*$|;)", "UPDATE without WHERE"),
    ("shutdown", r"shutdown\s+-[hr]\s+(?:now|\d+)", "System shutdown"),
    ("reboot", r"reboot\s*$", "System reboot"),
    ("sudo-rm-rf", r"sudo\s+rm\s+[-\/]*rf?", "sudo + rm -rf"),
    ("mkfs", r"mkfs\.\w+", "Filesystem creation"),
    ("docker-rm-f", r"docker\s+rm\s+.*-f", "Force remove containers"),
    ("docker-prune", r"docker\s+system\s+prune\s+-a", "Remove all unused resources"),
    ("kubectl-delete-all", r"kubectl\s+delete\s+.*--all", "Delete all resources"),
    ("terraform-destroy", r"terraform\s+destroy\s+.*-auto-approve", "Auto-approve destroy"),
]

def check_command(cmd, patterns=None):
    if not cmd: return False, None
    patterns = patterns or PATTERNS
    n = re.sub(r'\s+', ' ', cmd).strip()
    for name, regex, reason in patterns:
        if re.search(regex, n, re.IGNORECASE):
            return True, {"pattern": name, "command": n, "reason": reason,
                          "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                          "project": os.environ.get("CLAUDE_PROJECT_ROOT","unknown")}
    return False, None

def main():
    tool = os.environ.get("CLAUDE_TOOL_NAME","")
    if tool and tool != "Bash": sys.exit(0)
    raw = os.environ.get("CLAUDE_INPUT","")
    cmd = ""
    if raw:
        try: cmd = json.loads(raw).get("command","")
        except: cmd = raw
    if not cmd: sys.exit(0)
    blocked, info = check_command(cmd)
    if blocked:
        log = Path.home() / ".claude" / "hooks" / "blocked.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log,"a") as f: f.write(json.dumps(info)+"\n")
        print(f"\n⛔ BLOCKED - {info['pattern']}\n  {info['reason']}\n")
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__": main()
