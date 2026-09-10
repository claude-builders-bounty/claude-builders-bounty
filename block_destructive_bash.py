#!/usr/bin/env python3

import json
import re
import shlex
from pathlib import Path


LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def detect_dangerous(command):
    try:
        parts = shlex.split(command)
    except ValueError:
        return False, ""

    if not parts:
        return False, ""

    # Ignore harmless commands such as: echo rm -rf
    # Look at actual shell command segments.
    segments = re.split(r"\s*(?:&&|\|\||;|\|)\s*", command)

    for segment in segments:
        try:
            tokens = shlex.split(segment)
        except ValueError:
            continue

        if not tokens:
            continue

        # Allow simple echo of dangerous-looking text.
        if tokens[0] in ("echo", "printf"):
            continue

        # Find actual rm command, including sudo rm ...
        if "rm" in tokens:
            i = tokens.index("rm")
            args = tokens[i + 1:]

            has_r = any(
                token in ("-r", "-R") or
                (token.startswith("-") and not token.startswith("--")
                 and "r" in token[1:])
                for token in args
            )

            has_f = any(
                token in ("-f",) or
                (token.startswith("-") and not token.startswith("--")
                 and "f" in token[1:])
                for token in args
            )

            if has_r and has_f:
                return True, "recursive rm command"

        # git push --force / -f
        if len(tokens) >= 2 and tokens[0] == "git" and tokens[1] == "push":
            for token in tokens[2:]:
                if token == "--force" or token == "-f":
                    return True, "forced git push"

                # Explicitly allow --force-with-lease
                if token == "--force-with-lease":
                    continue

        upper = command.upper()

        if re.search(r"\bDROP\s+TABLE\b", upper):
            return True, "DROP TABLE command"

        if re.search(r"\bTRUNCATE\s+TABLE\b", upper):
            return True, "TRUNCATE command"

        if re.search(r"\bDELETE\s+FROM\b", upper):
            if not re.search(r"\bDELETE\s+FROM\b.*\bWHERE\b", upper):
                return True, "DELETE without WHERE"

    return False, ""


def write_log(command, cwd, reason):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    from datetime import datetime

    line = (
        f"{datetime.now().isoformat()} | "
        f"command={command!r} | "
        f"project={cwd!r} | "
        f"reason={reason}\n"
    )

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def main():
    try:
        payload = json.load(__import__("sys").stdin)
    except Exception:
        return 0

    command = (
        payload.get("tool_input", {}).get("command", "")
        if isinstance(payload, dict)
        else ""
    )

    cwd = payload.get("cwd", "") if isinstance(payload, dict) else ""

    dangerous, reason = detect_dangerous(command)

    if not dangerous:
        # IMPORTANT: Claude Code expects no output for allowed commands.
        return 0

    write_log(command, cwd, reason)

    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive command: {reason}"
            ),
        }
    }

    print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
