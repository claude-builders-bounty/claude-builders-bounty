#!/usr/bin/env python3
"""pre-tool-use hook for Claude Code: block dangerous bash commands.

Claude Code invokes PreToolUse hooks with JSON on stdin:
  {"tool_name": "...", "tool_input": {"command": "..."}}
A non-zero exit code BLOCKS the tool call; stdout (if any) is shown to the user.

Dangerous patterns blocked (with a clear reason):
  - rm -rf / , rm -rf ~, rm -rf * at root scope
  - git push --force / --no-verify on protected branches
  - :(){ :|:& };:  (fork bomb) and other obvious forkbombs
  - chmod -R 777 /, chown -R root /
  - curl|sh / wget|sh one-liners (pipe-to-shell installers)
  - dd of=/dev/... (disk wipe), mkfs, format
  - sudo su / su - (privilege escalation without intent)
"""
import json
import sys
import re

DANGEROUS = [
    (r"\brm\s+-rf\s+(/\s|~\s|/\*|/\s+--no-preserve-root)", "refusing recursive delete at filesystem root"),
    (r"\bgit\s+push\s+(--force|--no-verify)\b", "refusing forced / unverified push"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", "refusing fork-bomb pattern"),
    (r"\bchmod\s+-R\s+777\s+/", "refusing world-writable chmod on /"),
    (r"\bchown\s+-R\s+root\s+/", "refusing recursive chown to root on /"),
    (r"(curl|wget)\s+[^|]*\|\s*(sudo\s+)?(ba)?sh\b", "refusing pipe-to-shell installer"),
    (r"\bdd\s+.*of=/dev/", "refusing raw disk write (dd)"),
    (r"\bmkfs\b|\bformat\s+[a-z]", "refusing filesystem format"),
]

def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        # If we can't parse input, don't block — fail open.
        return 0

    if data.get("tool_name") != "Bash":
        return 0

    cmd = (data.get("tool_input") or {}).get("command", "") or ""
    for pat, reason in DANGEROUS:
        if re.search(pat, cmd):
            sys.stderr.write(f"BLOCKED by pre-tool-use hook: {reason}\n")
            sys.stderr.write(f"Command was: {cmd}\n")
            return 1  # non-zero => block

    return 0  # allow

if __name__ == "__main__":
    sys.exit(main())
