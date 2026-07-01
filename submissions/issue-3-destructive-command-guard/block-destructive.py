#!/usr/bin/env python3
"""
Claude Code PreToolUse hook — block destructive bash commands.

Reads the PreToolUse event JSON on stdin. If the tool is `Bash` and its command
matches a known-destructive pattern, the command is DENIED (Claude never runs it)
and the attempt is appended to ~/.claude/hooks/blocked.log.

Blocked patterns:
  - `rm -rf`            recursive + force delete (any flag spelling/order)
  - `git push --force`  force push (`--force` or `-f`; allows `--force-with-lease`)
  - `DROP TABLE`        (and `DROP DATABASE`)
  - `TRUNCATE`          table truncation
  - `DELETE FROM` ...   without a `WHERE` clause (unqualified mass delete)

Exit codes:
  0  — always (decision is communicated via JSON on stdout, the documented
       PreToolUse contract). A crash also exits 0 so the hook can never wedge
       your session; it fails open.
"""
import datetime
import json
import os
import re
import sys

HOOK_DIR = os.path.expanduser("~/.claude/hooks")
# Log destination — override with CLAUDE_HOOK_LOG (used by the test suite so it
# never touches your real log).
LOG_PATH = os.environ.get("CLAUDE_HOOK_LOG") or os.path.join(HOOK_DIR, "blocked.log")

# A command is a "segment" between shell separators (; | & newline). We test each
# segment so `ls && rm -rf /` is caught on its second segment only.
_SEG_SPLIT = re.compile(r"[\n;&|]+")


def _split_segments(command):
    return [s.strip() for s in _SEG_SPLIT.split(command) if s.strip()]


def _flags(seg):
    """Parse a command segment into (short_flag_chars, long_flag_names).

    Bundled short flags expand to individual chars, so `-rf` -> {'r', 'f'} and
    `-Rf` -> {'R', 'f'}. `--recursive` -> long name 'recursive'.
    """
    short, long = set(), set()
    for tok in seg.split():
        if tok.startswith("--") and len(tok) > 2:
            long.add(tok[2:])
        elif tok.startswith("-") and len(tok) > 1:
            short.update(tok[1:])
    return short, long


def _rm_rf(seg):
    # rm with BOTH a recursive flag and a force flag, in any spelling/order:
    #   -rf  -fr  -r -f  -Rf  --recursive --force  (bundled or separate)
    if not re.match(r"(?:sudo\s+)?rm\b", seg, re.I):
        return False
    short, long = _flags(seg)
    recursive = "r" in short or "R" in short or "recursive" in long
    force = "f" in short or "force" in long
    return recursive and force


def _force_push(seg):
    if not re.search(r"\bgit\s+push\b", seg, re.I):
        return False
    if "--force-with-lease" in seg:  # the safe variant — allow it
        return False
    short, long = _flags(seg)
    return "f" in short or "force" in long


def _drop(seg):
    return bool(re.search(r"\bDROP\s+(TABLE|DATABASE)\b", seg, re.I))


def _truncate(seg):
    return bool(re.search(r"\bTRUNCATE\b", seg, re.I))


def _delete_no_where(seg):
    # each DELETE FROM ... up to end of segment must contain a WHERE
    for m in re.finditer(r"\bDELETE\s+FROM\b(.*)$", seg, re.I | re.S):
        if not re.search(r"\bWHERE\b", m.group(1), re.I):
            return True
    return False


RULES = [
    ("rm -rf", "recursive force delete (`rm -rf`) — can wipe entire directory trees irreversibly", _rm_rf),
    ("git push --force", "force push (`git push --force`) — overwrites remote history for everyone; use `--force-with-lease` if you must", _force_push),
    ("DROP TABLE", "`DROP TABLE`/`DROP DATABASE` — permanently destroys a table/database and its data", _drop),
    ("TRUNCATE", "`TRUNCATE` — empties a table with no undo and no WHERE guard", _truncate),
    ("DELETE without WHERE", "`DELETE FROM` with no `WHERE` clause — deletes every row in the table", _delete_no_where),
]


def detect(command):
    """Return (rule_name, explanation) for the first matching rule, else None."""
    for seg in _split_segments(command):
        for name, why, test in RULES:
            if test(seg):
                return name, why
    return None


def log_block(command, project_path, rule_name):
    try:
        os.makedirs(HOOK_DIR, exist_ok=True)
        ts = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        line = f"{ts}\t[{rule_name}]\t{project_path}\t{command}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # logging must never break the hook
        pass


def main():
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except (ValueError, TypeError):
        return  # unparseable input — fail open, don't block

    if event.get("tool_name") != "Bash":
        return  # only guards Bash

    command = (event.get("tool_input") or {}).get("command", "") or ""
    if not command.strip():
        return

    hit = detect(command)
    if not hit:
        return  # normal command — stay out of the way

    rule_name, why = hit
    project_path = event.get("cwd") or os.getcwd()
    log_block(command, project_path, rule_name)

    message = (
        f"🛑 Blocked by destructive-command guard: {why}.\n"
        f"Matched rule: {rule_name}. Logged to {LOG_PATH}.\n"
        f"If this is genuinely intended, run it yourself in a terminal, or narrow "
        f"the command (e.g. add a WHERE clause, use --force-with-lease, or delete "
        f"specific paths instead of a recursive force wipe)."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
    sys.exit(0)
