#!/usr/bin/env python3
"""pre_tool_use.py — Claude Code Pre-Tool-Use Hook (cross-platform)
Blocks destructive bash commands before execution.
Install: copy to ~/.claude/hooks/pre-tool-use (or pre-tool-use.py on Windows)
"""
import sys, os, json, re, datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_PATTERNS = [
    (r"rm\s+-rf\s+/\s*$", "Recursive root deletion (rm -rf /)"),
    (r"rm\s+-rf\s+/\s*\*", "Recursive root wildcard deletion (rm -rf /*)"),
    (r"rm\s+-rf\s+/home\s*$", "Home directory deletion (rm -rf /home)"),
    (r"rm\s+-rf\s+--no-preserve-root", "Dangerous rm with no-preserve-root"),
    (r"dd\s+if=", "Disk destruction via dd"),
    (r"mkfs\.", "Filesystem formatting"),
    (r"fdisk\s+/dev", "Partition table modification"),
    (r"parted\s+/dev", "Partition editing"),
    (r">\s*/dev/sd", "Writing directly to block device"),
    (r"chmod\s+-R\s+777\s+/", "Permission bombing root"),
    (r":\(\)\s*\{", "Fork bomb detection"),
    (r"wget.*\|.*(?:bash|sh)", "wget pipe to shell (dangerous)"),
    (r"curl.*\|.*(?:bash|sh)", "curl pipe to shell (dangerous)"),
    (r"sudo\s+rm\s+-rf", "Escalated recursive deletion"),
    (r"mv\s+/\s+/dev/null", "Moving root to null"),
    (r"shutdown\s+(?:now|-h|-r|0)", "System shutdown in CI"),
    (r"\breboot\b", "System reboot"),
    (r"\bhault\b", "System halt"),
    (r"DROP\s+TABLE", "SQL table deletion"),
    (r"TRUNCATE\s+TABLE", "SQL table truncation"),
    (r"DELETE\s+FROM(?!.*(?:WHERE|where))", "SQL delete without WHERE clause"),
    (r"git\s+push\s+--force", "Force push to git"),
    (r"git\s+push\s+-f\b", "Force push to git (short form)"),
]


def check_command(cmd: str) -> bool:
    """Check if command is safe. Returns True if SAFE, False if BLOCKED."""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            print(f"[SECURITY] BLOCKED: {reason}", file=sys.stderr)
            print(f"[SECURITY] Command was: {cmd[:200]}", file=sys.stderr)
            print(f"[SECURITY] To disable: rm ~/.claude/hooks/pre-tool-use", file=sys.stderr)
            # Log the attempt
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            project = os.getcwd()
            with open(LOG_FILE, "a") as f:
                f.write(f"[{ts}] [BLOCKED] {reason} | project={project} | cmd={cmd[:200]}\n")
            return False
    return True


def main():
    cmd = None

    # Try to read from stdin (JSON tool call format)
    if not sys.stdin.isatty():
        try:
            input_data = json.loads(sys.stdin.read())
            if isinstance(input_data, dict):
                name = input_data.get("name", "")
                inp = input_data.get("input", {})
                if isinstance(inp, dict):
                    cmd = inp.get("command", inp.get("cmd", ""))
                elif isinstance(inp, str):
                    cmd = inp
        except (json.JSONDecodeError, Exception):
            pass

    # Fallback: command-line arguments
    if not cmd and len(sys.argv) > 1:
        cmd = " ".join(sys.argv[1:])

    if cmd and not check_command(cmd):
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
