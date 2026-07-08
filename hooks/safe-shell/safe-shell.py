#!/usr/bin/env python3
"""pre-tool-use hook - blocks dangerous bash commands before execution"""
import os, json, sys, re
from datetime import datetime

DANGEROUS = [
    (r"rm\s+-rf\s+/?(?:\s|$)", "recursive root delete"),
    (r"DROP\s+(DATABASE|TABLE)", "database drop"),
    (r"git\s+push\s+--force", "force push"),
    (r":\(\)\s*\{|fork bomb", "fork bomb"),
    (r"chmod\s+-R\s+0{4,}", "permission wipe"),
    (r"curl.*\|\s*bash", "pipe-to-shell"),
    (r"wget.*-O-\s*\|\s*sh", "pipe-to-shell"),
    (r"shutdown\s+-h\s+now", "shutdown"),
    (r"reboot", "reboot"),
]

LOG = os.path.expanduser("~/.claude/hooks/blocked.log")

def check(cmd):
    for pat, name in DANGEROUS:
        if re.search(pat, cmd, re.IGNORECASE):
            return {"blocked": True, "reason": name}
    return {"blocked": False}

def main():
    payload = json.loads(sys.stdin.read())
    tool = payload.get("toolUse", {})
    if tool.get("name") != "bash":
        print(json.dumps({"isApproved": True})); return
    cmd = tool.get("input", {}).get("command", "")
    r = check(cmd)
    if r["blocked"]:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a") as f:
            f.write(json.dumps({**r, "cmd": cmd[:200], "ts": datetime.now().isoformat()}) + "\n")
        print(json.dumps({"isApproved": False, "denialReason": f"Blocked: {r['reason']}"}))
    else:
        print(json.dumps({"isApproved": True}))

if __name__ == "__main__":
    main()
