#!/usr/bin/env python3
import datetime as _dt
import json
import os
import re
import sys


def read_event():
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Safe bash hook could not parse JSON input: {exc}", file=sys.stderr)
        sys.exit(1)


def compact(command):
    return re.sub(r"\s+", " ", command).strip()


def delete_from_without_where(command):
    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        tail = command[match.end():]
        statement = re.split(r";|&&|\|\||\n", tail, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def block_reason(command):
    normalized = compact(command)

    checks = [
        (r"\brm\s+(?:-[A-Za-z]*r[A-Za-z]*f|- [^\n]*|-[A-Za-z]*f[A-Za-z]*r)\b", "rm -rf can recursively delete files without confirmation"),
        (r"\bdrop\s+table\b", "DROP TABLE can permanently remove database tables"),
        (r"\bgit\s+push\b[^\n;]*\s--force(?:\s|$|=|-)", "git push --force can overwrite remote history"),
        (r"\btruncate\b", "TRUNCATE can delete table contents without row-level filtering"),
    ]

    for pattern, reason in checks:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return reason

    if delete_from_without_where(normalized):
        return "DELETE FROM without a WHERE clause can delete every row"

    return None


def log_block(command, cwd, reason):
    hooks_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    log_path = os.path.join(hooks_dir, "blocked.log")
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    line = json.dumps(
        {
            "timestamp": timestamp,
            "project_path": cwd,
            "attempted_command": command,
            "reason": reason,
        },
        sort_keys=True,
    )
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main():
    event = read_event()
    if event.get("hook_event_name") != "PreToolUse" or event.get("tool_name") != "Bash":
        sys.exit(0)

    command = event.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command.strip():
        sys.exit(0)

    reason = block_reason(command)
    if not reason:
        sys.exit(0)

    cwd = event.get("cwd") or os.getcwd()
    log_block(command, cwd, reason)
    print(
        "Blocked unsafe Bash command. "
        f"Reason: {reason}. "
        "Choose a safer command, narrow the target, add an explicit WHERE clause, "
        "or ask the user before performing destructive work.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
