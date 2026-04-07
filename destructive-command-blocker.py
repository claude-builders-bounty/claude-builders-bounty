#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands."""
import json, sys, re

BLOCKED_PATTERNS = [
    r'\brm\s+(-[rfvdi]*\s+)*/',          # rm at root
    r'\brm\s+-rf\s+[~$/]',               # rm -rf on home/root
    r'\brm\s+-rf\s+\.',                   # rm -rf .
    r'\bsudo\s+rm\b',                     # sudo rm
    r'\bmkfs\b',                           # format filesystem
    r'\bdd\s+.*of=/',                      # dd to device
    r'\b:(){ :\|:& };:',                   # fork bomb
    r'\bchmod\s+-R\s+777\s+/',            # chmod 777 root
    r'\bchown\s+-R.*/',                    # chown root
    r'\bgit\s+push.*--force\b',           # force push
    r'\bgit\s+reset\s+--hard\b',          # hard reset
    r'\bkill\s+-9\s+-1\b',               # kill all
    r'\bpkill\s+-9\s+',                   # kill by name
    r'\bcurl.*\|\s*(ba)?sh\b',            # pipe curl to shell
    r'\bwget.*\|\s*(ba)?sh\b',            # pipe wget to shell
    r'\b> /dev/sd[a-z]\b',               # write to disk device
    r'\bnc\s+.*-e\s+/bin/(ba)?sh\b',     # reverse shell
    r'\bshutdown\b',                      # shutdown
    r'\breboot\b',                        # reboot
    r'\binit\s+[06]\b',                   # init halt/reboot
    r'DROP\s+(TABLE|DATABASE)\b',          # SQL drop
    r'TRUNCATE\s+TABLE\b',                # SQL truncate
    r'DELETE\s+FROM\s+\w+\s*;?\s*$',     # DELETE without WHERE
]

ALLOWED_OVERRIDES = [
    r'\brm\s+(-[f]*\s+)?[\w./-]+\.(log|tmp|pyc|bak)$',  # Allow removing temp files
]

def check_command(cmd):
    cmd_lower = cmd.strip()
    for pattern in ALLOWED_OVERRIDES:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            return None
    for pattern in BLOCKED_PATTERNS:
        match = re.search(pattern, cmd_lower, re.IGNORECASE)
        if match:
            return f"BLOCKED: destructive command detected ({match.group()[:40]})"
    return None

def main():
    hook_input = json.loads(sys.stdin.read())
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name != "Bash":
        return

    command = tool_input.get("command", "")
    reason = check_command(command)
    if reason:
        result = {"decision": "block", "reason": reason}
    else:
        result = {"decision": "approve"}
    print(json.dumps(result))

if __name__ == "__main__":
    main()
