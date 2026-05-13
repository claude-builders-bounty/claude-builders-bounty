#!/usr/bin/env python3
"""Claude Code pre-tool-use hook — blocks destructive bash commands."""
import sys, re

def check_command(cmd: str) -> dict:
    blocked = [
        "rm -rf /", "rm -rf ~", "rm -rf .", "dd if=", "mkfs",
        ":(){ :|:& };:"
    ]
    dangerous = [
        r"(^|[;&|])rm\s+[-]?rf?\s", r"(^|[;&|])chmod\s+-R\s+777",
        r"(^|[;&|])chown\s+-R\s", r"(^|[;&|])git push --force",
        r"(^|[;&|])git reset --hard", r"\bsudo\s+",
        r"\bdrop\s+(table|database)\b", r"\btruncate\s+"
    ]
    cmd_lower = cmd.lower().strip()
    for b in blocked:
        if b in cmd_lower:
            return {"allowed": False, "reason": f"Command blocked: {b}"}
    for d in dangerous:
        if re.search(d, cmd_lower):
            return {"allowed": False, "reason": "Dangerous pattern detected"}
    return {"allowed": True}

if __name__ == "__main__":
    cmd = sys.stdin.read()
    import json
    print(json.dumps(check_command(cmd)))
