#!/usr/bin/env python3
"""
block_bash.py — Claude Code PreToolUse hook that blocks destructive bash commands.

Claude Code pipes the tool call as JSON on stdin. We either allow it (exit 0,
no output) or deny it (exit 0 + hookSpecificOutput deny, so Claude gets a clean
reason back) while appending an audit line to blocked.log.

No third-party dependencies: stdlib only, so it runs on any Python 3.9+.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

RM_RISK_DESCRIPTION = "recursive force delete of files (rm -rf and its flag-split variants)"

# (name, pattern, human explanation). `rm` is handled separately because the
# dangerous part is a *combination* of flags that can be spelled several ways:
# `-rf`, `-fr`, `-r --force`, `--recursive --force`, `-R -f`...
RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "drop-table",
        re.compile(r"\bDROP\s+(?:TEMPORARY\s+|EXTERNAL\s+)?TABLE\b", re.I),
        "DROP TABLE destroys a database schema and its data",
    ),
    (
        "git-force-push",
        re.compile(
            r"\bgit\b[^;&|\n]*\bpush\b(?=[^;&|\n]*\s-{1,2}(?:force\b|f\b))"  # --force / -f
            r"|\bgit\b[^;&|\n]*\bpush\b[^;&|\n]*\s\+\S",  # +ref:refs/heads/...
            re.I,
        ),
        "force push overwrites remote history (git push --force / +refspec)",
    ),
    (
        "truncate",
        re.compile(r"\bTRUNCATE\b", re.I),
        "TRUNCATE empties a table",
    ),
    (
        "delete-without-where",
        re.compile(r"\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)", re.I),
        "DELETE FROM without a WHERE clause wipes every row",
    ),
]

RM_RE = re.compile(
    r"(?:^|[;&|\n]\s*)\s*"
    r"(?:[A-Za-z_]\w*=\S+\s*)*"                             # VAR=value prefixes
    r"(?:(?:sudo|doas|env|command|nohup|time|nice|xargs|bash|sh|zsh|dash|ksh|eval)\s+)*"
    r"(?:(?:-{1,2}\S+)\s+)*"                              # flags like bash -c
    r"(?:\S*/)?rm(?=\s|$)",
    re.I,
)
def is_dangerous_rm(segment: str) -> bool:
    """`rm` is destructive only when recursive *and* forced are both present."""
    match = RM_RE.search(segment)
    if not match:
        return False
    tail = segment[match.end():].lstrip()
    recursive = forced = False
    for token in re.split(r"\s+", tail):
        token = token.strip(";\'\"")
        if not token:
            continue
        if not token.startswith("-") or token == "--":
            break  # first non-flag token is the target: the flags ended
        if token.startswith("--"):
            name = token[2:].split("=")[0].lower()
            if name == "recursive":
                recursive = True
            elif name == "force":
                forced = True
        else:
            letters = {c.lower() for c in token[1:]}
            if "r" in letters:
                recursive = True
            if "f" in letters:
                forced = True
    return recursive and forced


# Split on shell separators so `echo hi && rm -rf /` is still caught.
SEGMENT_SPLIT = re.compile(r"(?:&&|\|\||;|\||\n|&)")

# Commands whose job is to *show* text, not act on it. Matching a destructive
# pattern inside their arguments is a false positive, not an attack.
DISPLAY_COMMANDS = {"echo", "printf", "grep", "egrep", "rg", "cat", "head", "tail", "less", "man", "wc"}
WRAPPERS = {"env", "sudo", "command", "nohup", "time", "nice"}


def normalise(command: str) -> str:
    """Collapse quoting/expansion tricks that are used to smuggle a bad command past a regex."""
    text = command.replace("\\\n", " ")
    # Remove simple quoting so 'rm -rf' still matches, but keep the token boundaries intact.
    text = re.sub(r"[\"'`]", " ", text)
    # ${...} / $(...) expansions can hide arguments: drop the payload, keep the call.
    text = re.sub(r"\$\{[^}]*\}", " VAR ", text)
    text = re.sub(r"\$\([^)]*\)", " VAR ", text)
    text = re.sub(r"\$[A-Za-z_]\w*", " VAR ", text)
    return text


def is_display_only(segment: str) -> bool:
    """True when the segment only *prints* text (echo/grep/cat...), so a matched
    pattern is an argument, not something about to be executed."""
    tokens = segment.split()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if re.match(r"^[A-Za-z_]\w*=", tok) or tok in WRAPPERS:
            i += 1
            continue
        break
    return i < len(tokens) and os.path.basename(tokens[i]) in DISPLAY_COMMANDS


def find_violations(command: str) -> list[str]:
    hits: list[str] = []
    for segment in SEGMENT_SPLIT.split(normalise(command)):
        segment = segment.strip()
        if not segment or is_display_only(segment):
            continue
        for name, pattern, _why in RULES:
            if pattern.search(segment) and name not in hits:
                hits.append(name)
        if is_dangerous_rm(segment) and "rm-rf" not in hits:
            hits.append("rm-rf")
    return hits


def describe(names: list[str]) -> str:
    parts = []
    for name in names:
        if name == "rm-rf":
            parts.append(RM_RISK_DESCRIPTION)
            continue
        parts.extend(why for n, _pattern, why in RULES if n == name)
    return "; ".join(parts)


def write_log(command: str, names: list[str], project_dir: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        stamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(
                f"[{stamp}] blocked={','.join(names)} project={project_dir} command={command!r}\n"
            )
    except OSError:  # never let logging break the gate
        pass


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    project_dir = (
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )

    if not command:
        return 0

    names = find_violations(command)
    if not names:
        return 0  # allow silently

    write_log(command, names, project_dir)

    why = describe(names)
    message = (
        f"BLOCKED by block_bash.py: {why}. "
        "This command is destructive and was not executed. "
        "Rewrite it as a narrower command (target a specific path, add a WHERE "
        "clause, or use --force-with-lease), or ask the user to run it "
        "manually if they truly mean it."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
