#!/usr/bin/env python3
"""pre-tool-use hook for Claude Code"""
import os, sys, json, datetime
BLOCKED = [
    "rm -rf", "rm -fr", "rm --recursive",
    "DROP TABLE", "DROP DATABASE", "TRUNCATE TABLE",
    "git push --force", "git push -f",
    "DELETE FROM",
    "shutdown now", "shutdown -h",
    "dd if=", "mkfs.",
    "chmod 777",
    "wget.*sh",
]
LOG = os.path.expanduser("~/.claude/hooks/blocked.log")
def blocked(cmd):
    cl = cmd.lower()
    for p in BLOCKED:
        if p.lower() in cl:
            return True
    if "delete from" in cl and "where" not in cl:
        return True
    return False
def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        return
    cmd = data.get("command", "")
    if not blocked(cmd):
        print(json.dumps({"blocked": False}))
        return
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    ts = datetime.datetime.now().isoformat()
    with open(LOG, "a") as f:
        f.write(f"[{ts}] [{os.getcwd()}] {cmd}\n")
    print(json.dumps({"blocked": True, "message": "BLOCKED: " + cmd}))
if __name__ == "__main__":
    main()
