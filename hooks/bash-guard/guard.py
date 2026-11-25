"""Claude Code PreToolUse hook for Bash. Only inspect the incoming event."""

import datetime
import json
import os
from pathlib import Path
import re
import shlex
import sys


SQL_TOKEN = re.compile(
    r"""--[^\n]*|/\*[\s\S]*?\*/|'(?:''|[^'])*'|"(?:""|[^"])*"|`[^`]*`|\[[^\]]*\]|[A-Za-z_][\w$]*|[();]"""
)
SQL_CLIENTS = {"psql", "sqlite3", "mysql", "mariadb", "duckdb", "sqlcmd", "sqlplus"}


def sql_reason(sql):
    words = []
    depth = 0
    for match in SQL_TOKEN.finditer(sql + ";"):
        value = match.group()
        if value.startswith(("--", "/*")):
            continue
        if value == "(":
            depth += 1
        elif value == ")":
            depth = max(0, depth - 1)
        elif value == ";" and depth == 0:
            for index, word in enumerate(words):
                if word == "TRUNCATE":
                    return "The SQL statement truncates a table."
                if words[index:index + 2] == ["DROP", "TABLE"]:
                    return "The SQL statement drops a table."
                if words[index:index + 2] == ["DELETE", "FROM"] and "WHERE" not in words[index + 2:]:
                    return "The SQL DELETE has no top-level WHERE condition."
            words = []
        elif depth == 0:
            words.append(value.upper())
    return None


def command_reason(argv):
    while argv and (argv[0] in ("env", "command", "sudo") or re.match(r"^[a-zA-Z_]\w*=", argv[0])):
        argv = argv[1:]
    if not argv:
        return None
    name = os.path.basename(argv[0]).lower()
    args = argv[1:]
    if name == "rm":
        flags = []
        for arg in args:
            if arg == "--":
                break
            if arg.startswith("-"):
                flags.append(arg)
        short = "".join(x[1:] for x in flags if not x.startswith("--"))
        if ("f" in short or "--force" in flags) and (
            "r" in short or "R" in short or "--recursive" in flags
        ):
            return "Recursive forced removal can delete a whole directory tree."
    if name == "git":
        pos = 0
        while pos < len(args) and args[pos].startswith("-"):
            pos += 2 if args[pos] in ("-c", "-C", "--git-dir", "--work-tree", "--namespace") else 1
        if args[pos:pos + 1] == ["push"] and any(x in ("-f", "--force") for x in args[pos + 1:]):
            return "A forced Git push can replace remote history."
    if name in SQL_CLIENTS:
        for arg in args:
            reason = sql_reason(arg)
            if reason:
                return reason
    return None


def blocked_reason(command):
    if re.match(r"\s*(?:DROP|DELETE|TRUNCATE)\b", command, flags=re.I):
        return sql_reason(command)
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    argv = []
    literal_input = []
    for item in list(lex) + [";"]:
        if item and all(c in ";&|()\n" for c in item):
            reason = command_reason(argv)
            if not reason and argv and os.path.basename(argv[0]) in SQL_CLIENTS:
                reason = sql_reason(" ".join(literal_input))
            if reason:
                return reason
            literal_input = argv[1:] if item == "|" and argv and argv[0] in ("echo", "printf") else []
            argv = []
        else:
            argv.append(item)
    return None


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
          "permissionDecision": "deny", "permissionDecisionReason": reason}}))


def main():
    try:
        event = json.load(sys.stdin)
        if event.get("tool_name") != "Bash":
            return
        command = event["tool_input"]["command"]
        if not isinstance(command, str):
            raise ValueError("expected a command string")
        reason = blocked_reason(command)
    except (ValueError, KeyError, TypeError, AttributeError):
        deny("Cannot inspect this Bash event. Review the hook input and shell quoting.")
        return
    if reason:
        record = {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "command": command, "project_path": event.get("cwd"), "reason": reason}
        folder = Path.home() / ".claude" / "hooks"
        try:
            folder.mkdir(mode=0o700, parents=True, exist_ok=True)
            fd = os.open(folder / "blocked.log", os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "ab") as log:
                log.write((json.dumps(record, ensure_ascii=True) + "\n").encode())
        except OSError:
            reason += " The block log could not be written. Check its directory permissions."
        deny(reason)


if __name__ == "__main__":
    main()
