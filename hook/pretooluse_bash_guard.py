#!/usr/bin/env python3
"""pretooluse_bash_guard - Claude Code PreToolUse hook that blocks destructive bash commands.

The hook reads a PreToolUse JSON payload on stdin (format documented at
https://docs.anthropic.com/claude-code/hooks). When the payload is for the
Bash tool, the command is analyzed for destructive patterns:

  rule id            blocks
  ----------         ----------------------------------------------------------------
  rm-rf              recursive+force `rm` (e.g. `rm -rf /`). A small allowlist of
                     safe targets (node_modules, build, dist, ...) is excluded by
                     default; set HOOK_ALLOW_SAFE_RM_TARGETS=0 to disable it.
  drop-table         `DROP TABLE` (any case, incl. `DROP TABLE IF EXISTS ...`)
  truncate           `TRUNCATE [TABLE] <name>`
  delete-no-where    `DELETE FROM <table>` with no WHERE clause in the statement
  git-push-force     `git push --force` / `-f` (`--force-with-lease` is allowed)

On a match the hook:
  * appends one JSON line per rule to ~/.claude/hooks/blocked.log
    ({ts, command, cwd, rule, segment})
  * prints a clear reason to stderr (Claude sees it and adapts)
  * exits with code 2 so Claude Code blocks the command, and also prints
    {"decision":"block","reason":...} on stdout for newer clients

Everything else passes through untouched (exit 0). Python 3 stdlib only.

Environment configuration:
  HOOK_DISABLE_RULES          comma list of rule ids to disable (e.g. "truncate")
  HOOK_ALLOW_SAFE_RM_TARGETS  "1" (default) allows `rm -rf` on well-known build dirs
  HOOK_BLOCKED_LOG            override the blocked.log path (used by tests)

Note: SQL rules scan the fully-unquoted command line, so `echo "DROP TABLE x"`
is blocked by design (conservative). A false positive is cheap; a lost table is not.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

RULE_IDS = ("rm-rf", "drop-table", "truncate", "delete-no-where", "git-push-force")

# `rm -rf <target>` is allowed by default when every target is one of these.
SAFE_RM_TARGETS = {
    "node_modules", "build", "dist", "out", ".next", ".nuxt", ".turbo",
    ".cache", "__pycache__", ".pytest_cache", ".mypy_cache",
    "target", "bin", "obj", "coverage", ".venv", "venv",
}

_COMMAND_WRAPPERS = {"sudo", "env", "nohup", "nice", "time", "command"}

_SQL_RE_DROP_TABLE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
_SQL_RE_TRUNCATE = re.compile(r"\btruncate\s+(?:table\s+)?\w", re.IGNORECASE)
_SQL_RE_DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)


def default_log_path() -> Path:
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_path() -> Path:
    p = os.environ.get("HOOK_BLOCKED_LOG")
    return Path(p) if p else default_log_path()


def _disabled_rules() -> set:
    raw = os.environ.get("HOOK_DISABLE_RULES", "")
    return {d.strip() for d in raw.split(",") if d.strip()}


def split_segments(cmd: str) -> list:
    """Split a shell command into segments on ; && || | and subshell markers
    (backticks, $()), respecting single/double quotes."""
    segments = []
    cur = []
    quote = None
    i, n = 0, len(cmd)
    while i < n:
        c = cmd[i]
        if quote:
            cur.append(c)
            if c == quote and not (quote == '"' and len(cur) >= 2 and cur[-2] == "\\"):
                quote = None
        elif c in "\"'":
            quote = c
            cur.append(c)
        elif c == ";":
            segments.append("".join(cur).strip())
            cur = []
        elif c in "&|":
            segments.append("".join(cur).strip())
            cur = []
            if i + 1 < n and cmd[i + 1] == c:
                i += 1
        elif c == "`":
            segments.append("".join(cur).strip())
            cur = []
        elif c == "$" and i + 1 < n and cmd[i + 1] == "(":
            segments.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    segments.append("".join(cur).strip())
    return [s for s in segments if s]


def segment_tokens(seg: str):
    """shlex-split a segment; fall back to naive split on unbalanced quotes."""
    try:
        return shlex.split(seg, posix=True) or None
    except ValueError:
        return seg.split() or None


def _basename(tok: str) -> str:
    return tok.replace("\\", "/").rsplit("/", 1)[-1]


def _skip_wrappers(tokens, idx):
    """Advance past sudo/env/nohup/... prefixes; returns index of real command."""
    while idx < len(tokens) and _basename(tokens[idx]) in _COMMAND_WRAPPERS:
        if tokens[idx].replace("\\", "/").rsplit("/", 1)[-1] == "env":
            idx += 1
            while idx < len(tokens) and "=" in tokens[idx] and not tokens[idx].startswith("-"):
                idx += 1
        else:
            idx += 1
    return idx


def check_rm(tokens) -> bool:
    """True if this segment is a destructive recursive+force rm."""
    idx = _skip_wrappers(tokens, 0)
    if idx >= len(tokens) or _basename(tokens[idx]) != "rm":
        return False
    recursive = force = False
    targets = []
    for t in tokens[idx + 1:]:
        if t == "--":
            continue
        if t.startswith("-") and len(t) > 1:
            if t == "--recursive":
                recursive = True
            elif t == "--force":
                force = True
            elif not t.startswith("--"):
                body = t[1:]
                if "r" in body or "R" in body:
                    recursive = True
                if "f" in body:
                    force = True
        else:
            targets.append(t)
    if not (recursive and force):
        return False
    if os.environ.get("HOOK_ALLOW_SAFE_RM_TARGETS", "1") == "1" and targets:
        def norm(t):
            t = t.replace("\\", "/")
            t = re.sub(r"^\./", "", t)
            t = t.rstrip("/")
            return t
        if all(norm(t) in SAFE_RM_TARGETS for t in targets):
            return False
    return True


def check_git_push_force(tokens) -> bool:
    idx = _skip_wrappers(tokens, 0)
    if idx >= len(tokens) or _basename(tokens[idx]) != "git":
        return False
    args = tokens[idx + 1:]
    if "push" not in args:
        return False
    for t in args[args.index("push") + 1:]:
        if t == "--force" or t.startswith("--force="):
            return True
        if t.startswith("--force-with-lease"):
            continue
        if t.startswith("-") and not t.startswith("--") and len(t) > 1 and "f" in t[1:]:
            return True
    return False


def _flat_command(cmd: str) -> str:
    """Whole command with quotes stripped (all segments, all tokens)."""
    parts = []
    for seg in split_segments(cmd):
        parts.extend(segment_tokens(seg) or [])
    return " ".join(parts)


def check_sql(flat: str) -> list:
    """Return rule ids whose SQL pattern matches the unquoted command line."""
    hits = []
    if _SQL_RE_DROP_TABLE.search(flat):
        hits.append("drop-table")
    if _SQL_RE_TRUNCATE.search(flat):
        hits.append("truncate")
    m = _SQL_RE_DELETE_FROM.search(flat)
    if m:
        head = re.split(r";", flat[m.end():], 1)[0]
        if not re.search(r"\bwhere\b", head, re.IGNORECASE):
            hits.append("delete-no-where")
    return hits


_MESSAGES = {
    "rm-rf": ("BLOCKED (rm-rf): recursive+force rm is destructive. "
              "Use a plain non-recursive `rm <path>`, or target an allowlisted "
              "directory such as `rm -rf node_modules`."),
    "drop-table": ("BLOCKED (drop-table): `DROP TABLE` is irreversible. "
                   "Confirm with the user, or wrap it in a transaction you can roll back."),
    "truncate": ("BLOCKED (truncate): `TRUNCATE` removes every row irreversibly. "
                 "Confirm with the user before running it."),
    "delete-no-where": ("BLOCKED (delete-no-where): `DELETE FROM <table>` without a WHERE "
                        "clause deletes every row. Add a WHERE clause."),
    "git-push-force": ("BLOCKED (git-push-force): `git push --force` rewrites shared history. "
                       "Use `git push --force-with-lease` instead."),
}


def evaluate(cmd: str) -> list:
    """Return [(rule_id, message, segment)] for every rule that matches."""
    disabled = _disabled_rules()
    out = []
    seen = set()
    for seg in split_segments(cmd):
        toks = segment_tokens(seg)
        if not toks:
            continue
        if "rm-rf" not in disabled and "rm-rf" not in seen and check_rm(toks):
            out.append(("rm-rf", _MESSAGES["rm-rf"], seg))
            seen.add("rm-rf")
        if "git-push-force" not in disabled and "git-push-force" not in seen and check_git_push_force(toks):
            out.append(("git-push-force", _MESSAGES["git-push-force"], seg))
            seen.add("git-push-force")
    flat = _flat_command(cmd)
    for rule in check_sql(flat):
        if rule not in disabled and rule not in seen:
            out.append((rule, _MESSAGES[rule], cmd))
            seen.add(rule)
    return out


def run(payload) -> int:
    """Handle one PreToolUse payload. Returns 0 (allow) or 2 (block)."""
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input") or {}
    cmd = tool_input.get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        return 0
    cwd = payload.get("cwd") or tool_input.get("cwd") or ""
    hits = evaluate(cmd)
    if not hits:
        return 0
    try:
        lp = log_path()
        lp.parent.mkdir(parents=True, exist_ok=True)
        with lp.open("a", encoding="utf-8") as f:
            for rule, _msg, segment in hits:
                f.write(json.dumps({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "command": cmd,
                    "cwd": cwd,
                    "rule": rule,
                    "segment": segment,
                }, ensure_ascii=False) + "\n")
    except OSError:
        pass  # a logging failure must not break the block decision
    reasons = " ".join(msg for _rule, msg, _seg in hits)
    print(reasons, file=sys.stderr)
    print(json.dumps({"decision": "block", "reason": reasons}))
    return 2


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return 0  # malformed stdin: never interfere
    return run(payload)


if __name__ == "__main__":
    sys.exit(main())
