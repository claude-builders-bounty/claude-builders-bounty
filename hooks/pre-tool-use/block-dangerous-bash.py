#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive bash commands.

Reads Claude Code hook JSON from stdin. If the tool is Bash and the command
looks destructive, exits non-zero with a clear reason. Otherwise exits 0.
"""
import json
import re
import shlex
import sys

DANGEROUS_PATTERNS = [
    (r"\brm\s+(?:-[^\n;|&]*[rf][^\n;|&]*|-[^\n;|&]*[fr][^\n;|&]*)\s+(?:/|~|\$HOME|\.\.?)(?:\s|$)", "recursive/forced rm against broad path"),
    (r"\bsudo\s+rm\s+(?:-[^\n;|&]*[rf][^\n;|&]*|-[^\n;|&]*[fr][^\n;|&]*)", "sudo recursive/forced rm"),
    (r"\bmkfs(?:\.[a-z0-9]+)?\b", "filesystem formatting"),
    (r"\bdd\b[^\n;|&]*\bof=/dev/(?:sd|vd|nvme|xvd|hd)", "raw disk overwrite with dd"),
    (r"\bchmod\s+-R\s+777\s+(?:/|~|\$HOME|\.\.?)(?:\s|$)", "broad chmod 777"),
    (r"\bchown\s+-R\b[^\n;|&]*(?:\s/|\s~|\s\$HOME)(?:\s|$)", "broad recursive chown"),
    (r"\b(?:shutdown|reboot|poweroff|halt)\b", "system shutdown/reboot"),
    (r">\s*/dev/(?:sd|vd|nvme|xvd|hd)", "redirecting output to raw disk"),
]

ALLOW_HINT = "If intentional, ask the user for explicit approval and run a narrower command."


def get_command(payload: dict) -> str:
    if payload.get("tool_name") != "Bash":
        return ""
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or "")
    return ""


def strip_quoted(command: str) -> str:
    # Keep operators/words, remove quoted text to reduce false positives in echo/docs.
    try:
        tokens = shlex.split(command, comments=False, posix=True)
        return " ".join(tokens)
    except ValueError:
        return command


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook JSON: {exc}", file=sys.stderr)
        return 0

    command = get_command(payload)
    if not command:
        return 0

    normalized = strip_quoted(command)
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            print(f"Blocked dangerous Bash command: {reason}. {ALLOW_HINT}", file=sys.stderr)
            print(f"Command: {command}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
