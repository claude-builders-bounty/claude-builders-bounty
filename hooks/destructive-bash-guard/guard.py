#!/usr/bin/env python3
"""
Claude Code PreToolUse hook — blocks destructive bash commands.

Reads tool call JSON from stdin. Exits 2 (blocking) if the command matches
a destructive pattern. Logs every blocked attempt to ~/.claude/hooks/blocked.log.

Usage (via ~/.claude/settings.json):
  {
    "hooks": {
      "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/guard.py"}]}]
    }
  }
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Pre-compiled patterns for _is_rm_rf.
# Lookbehind (`(?<=\s)`) scoped around the entire alternation to require whitespace before
# any flag cluster — prevents matching flags embedded in filenames like `rm file-rf.txt`.
# No trailing lookahead so multi-flag clusters like -rfv are caught correctly.
_RE_RM_SEGMENT = re.compile(r'(?i)\brm\b([^|;&\n]*)')
_WS_OR_QUOTE = r'(?:(?<=\s)|(?<=["\']))'
_RE_RM_COMBINED = re.compile(
    _WS_OR_QUOTE + r'(?:-[a-zA-Z]*[rR][a-zA-Z]*[fF]|-[a-zA-Z]*[fF][a-zA-Z]*[rR])'
)
_RE_RM_RECURSIVE = re.compile(_WS_OR_QUOTE + r'(?:-[a-zA-Z]*[rR])|--recursive\b')
_RE_RM_FORCE = re.compile(_WS_OR_QUOTE + r'(?:-[a-zA-Z]*[fF])|--force\b')

# Pre-compiled patterns for check_delete_without_where.
_RE_DELETE_FROM = re.compile(r'(?i)\bDELETE\s+FROM\b')
_RE_WHERE = re.compile(r'(?i)\bWHERE\b')


def _is_rm_rf(cmd: str) -> bool:
    """Detect rm with both recursive and force flags in any order/combination."""
    # Check every rm segment separately (handles chained commands like `rm safe.txt; rm -rf /`).
    for match in _RE_RM_SEGMENT.finditer(cmd):
        segment = match.group(0)
        if _RE_RM_COMBINED.search(segment):
            return True
        has_recursive = bool(_RE_RM_RECURSIVE.search(segment))
        has_force = bool(_RE_RM_FORCE.search(segment))
        if has_recursive and has_force:
            return True
    return False


PATTERNS: List[Tuple[str, str]] = [
    # rm -rf handled separately via _is_rm_rf() above
    (r'(?i)\bDROP\s+TABLE\b', 'DROP TABLE (destructive SQL)'),
    (r'(?i)\bDROP\s+DATABASE\b', 'DROP DATABASE (destructive SQL)'),
    (r'(?i)\bTRUNCATE\s+(?:TABLE\s+)?\S', 'TRUNCATE TABLE (destructive SQL)'),
    (r'(?i)\bgit\b[^|;&\n]*?\bpush\b[^|;&\n]*?(-[a-zA-Z]*f\b|--force\b|--force-with-lease\b|--delete\b|-[a-zA-Z]*d\b|\s\+\S|\s:\S)', 'git push --force (history rewrite)'),
    (r'(?i)\bgit\b[^|;&\n]*?\breset\b[^|;&\n]*--hard\b', 'git reset --hard (discards uncommitted changes)'),
]


def check_delete_without_where(cmd: str) -> Optional[str]:
    """Return pattern name if any DELETE FROM statement lacks a WHERE clause.

    Splits on shell control operators and semicolons so a WHERE in a later
    command cannot shield an unbounded DELETE in an earlier one.
    """
    for stmt in re.split(r';|&&|&|\|\||\||\n', cmd):
        if _RE_DELETE_FROM.search(stmt) and not _RE_WHERE.search(stmt):
            return 'DELETE FROM without WHERE (unbounded row deletion)'
    return None


def _safe_log_str(value: str) -> str:
    """Escape a string for safe embedding in the structured log line."""
    return (
        value
        .replace('\\', '\\\\')
        .replace('\r', '\\r')
        .replace('\n', '\\n')
        .replace('"', '\\"')
    )


def log_blocked(pattern_name: str, project: str, cmd: str) -> None:
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry = (
        f'[{ts}] BLOCKED'
        f' | pattern="{_safe_log_str(pattern_name)}"'
        f' | project="{_safe_log_str(project)}"'
        f' | cmd="{_safe_log_str(cmd)}"\n'
    )
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open('a', encoding='utf-8') as f:
            f.write(entry)
    except OSError as exc:
        print(f"guard.py: could not write to log ({exc})", file=sys.stderr)


def block(pattern_name: str, project: str, cmd: str) -> None:
    log_blocked(pattern_name, project, cmd)
    msg = (
        f"BLOCKED: Destructive command detected\n"
        f"Pattern: {pattern_name}\n"
        f"Command: {cmd}\n"
        f"Project: {project}\n\n"
        "This command has been blocked to prevent accidental data loss.\n"
        "To proceed intentionally, use a safer alternative (e.g., move to trash, dry-run first)."
    )
    print(msg, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"guard.py: unexpected non-JSON input ({exc}) — blocking as a precaution", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, dict) or data.get("tool_name") != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input")
    cmd: str = str(tool_input.get("command") or "") if isinstance(tool_input, dict) else ""
    project: str = str(data.get("cwd", "unknown" ))

    if not cmd:
        sys.exit(0)

    # Strip bash line continuations (backslash-newline) before pattern matching.
    cmd = cmd.replace('\\\r\n', '').replace('\\\n', '')

    # Check rm -rf (handles combined and separated flags across all rm segments)
    if _is_rm_rf(cmd):
        block('rm -rf (recursive force delete)', project, cmd)

    # Check static patterns
    for pattern, name in PATTERNS:
        if re.search(pattern, cmd):
            block(name, project, cmd)

    # Check DELETE FROM without WHERE (per-statement check)
    delete_match = check_delete_without_where(cmd)
    if delete_match:
        block(delete_match, project, cmd)

    # Safe — allow
    sys.exit(0)


if __name__ == "__main__":
    main()
