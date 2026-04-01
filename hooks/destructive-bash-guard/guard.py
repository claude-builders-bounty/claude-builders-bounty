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

# ---------------------------------------------------------------------------
# rm -rf detection
# ---------------------------------------------------------------------------
# Extract everything after each `rm` invocation up to the next shell operator.
_RE_RM_SEGMENT = re.compile(r'(?i)\brm\b([^|;&\n]*)')
# Short flags like -rf, -fr, -Rfv, etc.
_RE_SHORT_FLAGS = re.compile(r'(?<!-)-([a-zA-Z]+)')  # negative lookbehind excludes --long-flags
_RE_LONG_RECURSIVE = re.compile(r'--recursive\b')
_RE_LONG_FORCE = re.compile(r'--force\b')


def _is_rm_rf(cmd: str) -> bool:
    """Detect rm with both recursive and force flags in any order/combination.

    Checks every rm segment separately so chained commands like
    `rm safe.txt; rm -rf /` are each evaluated independently.
    Uses simple flag-letter extraction to avoid ReDoS-prone alternation.
    """
    for match in _RE_RM_SEGMENT.finditer(cmd):
        segment = match.group(1)  # text after 'rm', before next operator
        # Collect all letters from all short flag groups (e.g. -rfv → 'rfv')
        flag_letters = ''.join(m.group(1) for m in _RE_SHORT_FLAGS.finditer(segment)).lower()
        has_r = 'r' in flag_letters or bool(_RE_LONG_RECURSIVE.search(segment))
        has_f = 'f' in flag_letters or bool(_RE_LONG_FORCE.search(segment))
        if has_r and has_f:
            return True
    return False


# ---------------------------------------------------------------------------
# Static regex patterns
# ---------------------------------------------------------------------------
PATTERNS: List[Tuple[str, str]] = [
    # rm -rf handled separately via _is_rm_rf() above
    (r'(?i)\bDROP\s+TABLE\b',    'DROP TABLE (destructive SQL)'),
    (r'(?i)\bDROP\s+DATABASE\b', 'DROP DATABASE (destructive SQL)'),
    # Require TABLE keyword — avoids false positive on the UNIX `truncate` file utility
    (r'(?i)\bTRUNCATE\s+TABLE\b', 'TRUNCATE TABLE (destructive SQL)'),
    # git push --force variants
    (r'(?i)\bgit\b[^|;&\n]*?\bpush\b[^|;&\n]*?(-[a-zA-Z]*f\b|--force\b|--force-with-lease\b|--delete\b|-[a-zA-Z]*d\b|\s["\']?\+\S|\s["\']?:\S)',
     'git push --force (history rewrite)'),
    (r'(?i)\bgit\b[^|;&\n]*?\breset\b[^|;&\n]*--hard\b',
     'git reset --hard (discards uncommitted changes)'),
    # Fork bomb
    (r':\(\)\s*\{', 'fork bomb (process resource exhaustion)'),
    # mkfs and low-level format utilities
    (r'(?i)\b(mkfs|mke2fs|mkswap|mkdosfs|mformat)\b', 'filesystem format utility'),
    # dd writing to a real block device (whitelist /dev/null and /dev/zero which are safe)
    (r'(?i)\bdd\b[^|;&\n]*\bof=["\']?/dev/(?!null\b|zero\b)', 'dd writing to device (disk wipe)'),
    # Pipe-to-shell — curl/wget output piped into any common shell (bash, sh, zsh, ksh, dash, fish)
    (r'(?i)\b(curl|wget)\b[^|;&\n]*\|[^|;&\n]*(ba|z|k|da|fi)?sh\b', 'pipe-to-shell (remote code execution)'),
]

# ---------------------------------------------------------------------------
# Commands dangerous only when they ARE the command, not an argument.
# Checked via token-based segment splitting to avoid false positives on e.g.
# `grep 'reboot' log.txt` or `echo shutdown`.
# ---------------------------------------------------------------------------
_POWER_COMMANDS = frozenset({'shutdown', 'poweroff', 'halt', 'reboot'})
_SYSTEMCTL_POWER = frozenset({'reboot', 'poweroff', 'halt', 'suspend', 'hibernate'})


def _first_real_token(tokens: List[str]) -> str:
    """Return the basename of the first executable token in a command segment.

    Skips: sudo, sudo flags (with their arguments where applicable),
    environment variable assignments (FOO=bar), and resolves path-qualified
    commands (/sbin/reboot → reboot) to defeat simple bypass attempts.
    """
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        tok_lower = tok.lower()
        # Skip sudo itself
        if tok_lower == 'sudo':
            i += 1
            continue
        # Skip env var assignments like FOO=bar or PATH=/usr/local/bin:$PATH
        if '=' in tok and not tok.startswith('-'):
            i += 1
            continue
        # Skip sudo flags; -u and -g take a following argument
        if tok.startswith('-'):
            if tok in ('-u', '-g', '--user', '--group') and i + 1 < len(tokens):
                i += 2
            else:
                i += 1
            continue
        # Return basename so /sbin/reboot → reboot, /bin/rm → rm
        return tok.split('/')[-1].lower()
    return ''


def check_power_command(cmd: str) -> Optional[str]:
    """Return pattern name if any segment starts with a system power/halt command."""
    for segment in re.split(r'[|;&\n]', cmd):
        tokens = segment.strip().split()
        if not tokens:
            continue
        first = _first_real_token(tokens)
        if first in _POWER_COMMANDS:
            return f'{first} (system power command)'
        # systemctl reboot/poweroff/halt/suspend
        # Find 'systemctl' in the segment and inspect the next non-flag token after it.
        if first == 'systemctl':
            lowered = [t.lower() for t in tokens]
            try:
                sc_idx = next(
                    i for i, t in enumerate(lowered)
                    if t.split('/')[-1] == 'systemctl'
                )
                subcmd = next(
                    t for t in lowered[sc_idx + 1:]
                    if not t.startswith('-') and '=' not in t
                )
                if subcmd in _SYSTEMCTL_POWER:
                    return f'systemctl {subcmd} (system power command)'
            except StopIteration:
                pass
    return None


# ---------------------------------------------------------------------------
# sudo rm — token-based to handle flags between sudo and rm
# ---------------------------------------------------------------------------
def check_sudo_rm(cmd: str) -> Optional[str]:
    """Return pattern name if any segment runs rm under sudo.

    Uses _first_real_token to resolve the actual executable (handles env var
    prefixes like `FOO=bar sudo rm`) and separately verifies sudo is present.
    """
    for segment in re.split(r'[|;&\n]', cmd):
        tokens = segment.strip().split()
        if not tokens:
            continue
        real = _first_real_token(tokens)
        if real != 'rm':
            continue
        # Confirm sudo appears before rm in this segment
        has_sudo = any(t.lower().split('/')[-1] == 'sudo' for t in tokens)
        if has_sudo:
            return 'sudo rm (privileged delete)'
    return None


# ---------------------------------------------------------------------------
# DELETE FROM without WHERE
# ---------------------------------------------------------------------------
_RE_DELETE_FROM = re.compile(r'(?i)\bDELETE\s+FROM\b')
_RE_WHERE = re.compile(r'(?i)\bWHERE\b')


def check_delete_without_where(cmd: str) -> Optional[str]:
    """Return pattern name if any DELETE FROM statement lacks a WHERE clause.

    Splits only on shell control operators (not newlines) so that a valid
    multi-line SQL query like `DELETE FROM t\\nWHERE id=1` is not falsely blocked.
    """
    for stmt in re.split(r';|&&|\|\|', cmd):
        if _RE_DELETE_FROM.search(stmt) and not _RE_WHERE.search(stmt):
            return 'DELETE FROM without WHERE (unbounded row deletion)'
    return None


# ---------------------------------------------------------------------------
# Logging and blocking
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except ValueError as exc:
        print(f"guard.py: unexpected non-JSON input ({exc}) — blocking as a precaution", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, dict) or data.get("tool_name") != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input")
    cmd: str = str(tool_input.get("command") or "") if isinstance(tool_input, dict) else ""
    project: str = str(data.get("cwd", "unknown"))

    if not cmd:
        sys.exit(0)

    # Strip bash line continuations (backslash-newline) before pattern matching.
    cmd = cmd.replace('\\\r\n', '').replace('\\\n', '')

    # rm -rf (handles combined and separated flags, all rm segments in chained commands)
    if _is_rm_rf(cmd):
        block('rm -rf (recursive force delete)', project, cmd)

    # sudo rm (token-based, handles sudo flags like -u root)
    sudo_rm = check_sudo_rm(cmd)
    if sudo_rm:
        block(sudo_rm, project, cmd)

    # Static regex patterns
    for pattern, name in PATTERNS:
        if re.search(pattern, cmd):
            block(name, project, cmd)

    # DELETE FROM without WHERE (per-statement, splits on shell operators not newlines)
    delete_match = check_delete_without_where(cmd)
    if delete_match:
        block(delete_match, project, cmd)

    # System power commands (token-based, avoids false positives on arguments)
    power_match = check_power_command(cmd)
    if power_match:
        block(power_match, project, cmd)

    sys.exit(0)


if __name__ == "__main__":
    main()
