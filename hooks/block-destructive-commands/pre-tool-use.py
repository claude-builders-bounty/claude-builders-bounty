#!/usr/bin/env python3
"""Claude Code PreToolUse hook — blocks destructive bash commands.

Detects destructive patterns in bare commands, chained segments (; && ||),
pipeline stages, shell -c wrappers, and container exec invocations
(docker/podman/kubectl exec and docker compose exec).
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

BLOCKED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bgit\b.*?\bpush\b.*?\s--force(?!\-\w)", re.IGNORECASE),
        "Git force push (git push --force)",
    ),
    (
        re.compile(r"\bgit\b.*?\bpush\b.*?\s-f\b", re.IGNORECASE),
        "Git force push (git push -f)",
    ),
]

# SQL TRUNCATE — exclude hyphen/underscore command names (e.g. npm run truncate-logs).
TRUNCATE_SQL = re.compile(r"\btruncate\b(?![-/_\w])", re.IGNORECASE)
# Unix truncate(1) uses flag options; avoid blocking file truncation utilities.
TRUNCATE_UTIL = re.compile(r"\btruncate\s+(?:-[a-zA-Z]|--)", re.IGNORECASE)

DELETE_FROM = re.compile(r"delete\s+from", re.IGNORECASE)
WHERE_CLAUSE = re.compile(r"\bwhere\b", re.IGNORECASE)
SQL_CLIENT = re.compile(
    r"\b(?:sqlite3|psql|mysql|mariadb|sqlcmd|mysqladmin)\b",
    re.IGNORECASE,
)
NON_SQL_TOOLS = re.compile(
    r"^\s*(?:echo|cat|printf|tee|grep|egrep|fgrep|rg|sed|awk|python3?|node|ruby|perl|head|tail|less|more|vim|nvim)\b",
    re.IGNORECASE,
)
SHELL_C = re.compile(
    r"\b(?:sh|bash|zsh|dash)\s+-c\s+(?:'([^']*)'|\"([^\"]*)\"|(\S+))",
    re.IGNORECASE,
)
GIT_FORCE_REFSPEC = re.compile(
    r"\bgit\b.*?\bpush\b(?:\s+[^\s;|&]+)*\s+\+[^\s;|&]+",
    re.IGNORECASE,
)
DD_DISK = re.compile(r"\bdd\b.*\bof=/dev/", re.IGNORECASE)
FORK_BOMB = re.compile(r":\(\s*\)\s*\{.*:\s*\|.*:.*&.*\}")
MKFS = re.compile(r"\bmkfs(?:\.\w+)?\b", re.IGNORECASE)
DEV_REDIRECT = re.compile(
    r">\s*/dev/(?:sd|hd|nvme|mmcblk|vd|xvd)",
    re.IGNORECASE,
)
WIPEFS = re.compile(r"\bwipefs\b", re.IGNORECASE)
REMOTE_SHELL = re.compile(
    r"\b(?:curl|wget)\b[^\n;|&]*\|\s*(?:ba)?sh\b",
    re.IGNORECASE,
)
DROP_TABLE = re.compile(r"drop\s+table", re.IGNORECASE)
DROP_DATABASE = re.compile(r"drop\s+database", re.IGNORECASE)
DROP_SCHEMA = re.compile(r"drop\s+schema", re.IGNORECASE)
GIT_RESET_HARD = re.compile(r"\bgit\b.*?\breset\b.*?\s--hard\b", re.IGNORECASE)
GIT_PUSH_FORCE_CONFIG = re.compile(
    r"-c\s+push\.force(?:\s*=\s*(?P<val>[^\s;|&]+))?",
    re.IGNORECASE,
)
GIT_PUSH_FORCE_CONFIG_FALSE = frozenset({"false", "0", "no", "off", "n"})
CHAIN_SPLIT = re.compile(r"\s*(?:;|&&|\|\|)\s*")
CONTAINER_RUNTIME_EXEC = re.compile(
    r"\b(?:docker(?:\s+compose)?|podman|kubectl|nerdctl)\s+exec\b",
    re.IGNORECASE,
)
CONTAINER_NAME = re.compile(r"^(?:[^\s\"']+|\"[^\"]*\"|'[^']*')\s*")


def normalize_command(command: str) -> str:
    """Strip padding and neutralize null bytes that can split regex tokens."""
    normalized = command.strip()
    if "\x00" not in normalized:
        return normalized
    normalized = normalized.replace("\x00", " ")
    return re.sub(r" +", " ", normalized).strip()


def iter_command_segments(command: str) -> list[str]:
    """Split chained bash commands so each segment is checked independently."""
    return [segment.strip() for segment in CHAIN_SPLIT.split(command) if segment.strip()]


def is_git_force_via_config(command: str) -> bool:
    """True when git -c push.force enables force push (not explicit false values)."""
    if not re.search(r"\bgit\b", command, re.IGNORECASE):
        return False
    if not re.search(r"\bpush\b", command, re.IGNORECASE):
        return False
    for match in GIT_PUSH_FORCE_CONFIG.finditer(command):
        value = (match.group("val") or "").strip().lower().strip("'\"")
        if value not in GIT_PUSH_FORCE_CONFIG_FALSE:
            return True
    return False


def stripped_segment(segment: str) -> str:
    """Remove leading sudo/env prefixes so bare SQL statements are detectable."""
    stripped = segment.strip()
    stripped = re.sub(r"^\s*sudo\s+", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"^(\w+=\S*\s+)+", "", stripped)
    return stripped


def embedded_shell_sql(segment: str, pattern: re.Pattern[str]) -> bool:
    """True when a shell -c wrapper embeds a matching SQL statement."""
    match = SHELL_C.search(segment)
    if not match:
        return False
    inner = next(group for group in match.groups() if group is not None)
    return bool(pattern.search(inner))


def iter_pipe_stages(segment: str) -> list[str]:
    """Split pipeline stages so rm -rf after a display tool is still detected."""
    return [stage.strip() for stage in segment.split("|") if stage.strip()]


def extract_container_exec_inner(segment: str) -> str | None:
    """Return the command run inside docker/podman/kubectl/nerdctl exec."""
    match = CONTAINER_RUNTIME_EXEC.search(segment)
    if not match:
        return None
    tail = segment[match.end() :].strip()
    while tail:
        if tail.startswith("-- "):
            tail = tail[3:].strip()
            break
        if flag_match := re.match(r"--[\w-]+=\S+\s*", tail):
            tail = tail[flag_match.end() :].strip()
            continue
        if flag_match := re.match(r"--[\w-]+\s+", tail):
            tail = tail[flag_match.end() :].strip()
            if tail and not tail.startswith("-"):
                value_match = re.match(r"\S+\s*", tail)
                if value_match:
                    tail = tail[value_match.end() :].strip()
            continue
        if flag_match := re.match(r"-\w+\s+", tail):
            flag_chars = flag_match.group().strip()[1:]
            tail = tail[flag_match.end() :].strip()
            if (
                len(flag_chars) == 1
                and tail
                and not tail.startswith("-")
            ):
                value_match = re.match(r"\S+\s*", tail)
                if value_match:
                    tail = tail[value_match.end() :].strip()
            continue
        break
    name_match = CONTAINER_NAME.match(tail)
    if not name_match:
        return None
    inner = tail[name_match.end() :].strip()
    if inner.startswith("-- "):
        inner = inner[3:].strip()
    return inner or None


def iter_segment_candidates(segment: str) -> list[str]:
    """Check the segment and any inner container exec command independently."""
    candidates = [segment]
    inner = extract_container_exec_inner(segment)
    if inner:
        candidates.append(inner)
    return candidates


def embedded_shell_rm_rf(segment: str) -> bool:
    """True when a shell -c wrapper embeds rm -rf."""
    match = SHELL_C.search(segment)
    if not match:
        return False
    inner = next(group for group in match.groups() if group is not None)
    return is_rm_rf(inner)


def segment_has_rm_rf_invocation(segment: str) -> bool:
    """Block rm -rf only when rm is executed, not when echoed or searched."""
    if embedded_shell_rm_rf(segment):
        return True
    for stage in iter_pipe_stages(segment):
        if NON_SQL_TOOLS.match(stage):
            continue
        if is_rm_rf(stage):
            return True
    return False


def should_block_sql_statement(
    segment: str,
    pattern: re.Pattern[str],
    *,
    util_exclude: re.Pattern[str] | None = None,
) -> bool:
    """Block SQL only in execution contexts, not search/display utilities."""
    if not pattern.search(segment):
        return False
    if util_exclude and util_exclude.search(segment):
        return False
    if SQL_CLIENT.search(segment):
        return True
    if embedded_shell_sql(segment, pattern):
        return True
    if NON_SQL_TOOLS.match(segment):
        return False
    return bool(pattern.match(stripped_segment(segment)))


_RM_RECURSIVE_FLAG = re.compile(
    r"(?:--recursive\b|(?<=\s)-[A-Za-z]*r[A-Za-z]*\b)",
    re.IGNORECASE,
)
_RM_FORCE_FLAG = re.compile(
    r"(?:--force\b|(?<=\s)-[A-Za-z]*f[A-Za-z]*\b)",
    re.IGNORECASE,
)


def is_rm_rf(command: str) -> bool:
    """True when rm uses both recursive (-r/--recursive) and force (-f/--force) flags."""
    if not re.search(r"\brm\b", command, re.IGNORECASE):
        return False
    after_rm = re.split(r"\brm\b", command, maxsplit=1, flags=re.IGNORECASE)[-1]
    return bool(_RM_RECURSIVE_FLAG.search(after_rm) and _RM_FORCE_FLAG.search(after_rm))


def sanitize_log_field(value: str) -> str:
    """Prevent log injection by escaping newlines and stripping control chars."""
    if not value:
        return ""
    sanitized = value.replace("\\", "\\\\")
    sanitized = sanitized.replace("\r", "\\r").replace("\n", "\\n")
    sanitized = sanitized.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return "".join(
        ch if (ch == "\t" or 32 <= ord(ch) <= 126) else "?" for ch in sanitized
    )


def log_blocked_attempt(command: str, project_path: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    safe_command = sanitize_log_field(command)
    safe_project_path = sanitize_log_field(project_path)
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(
            f"[{timestamp}] Command: {safe_command} | Project: {safe_project_path}\n"
        )


def deny(reason: str) -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


def check_segment_body(segment: str) -> str | None:
    if segment_has_rm_rf_invocation(segment):
        return "Recursive force delete (rm -rf)"

    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(segment):
            return reason

    if should_block_sql_statement(segment, DROP_TABLE):
        return "SQL DROP TABLE"

    if should_block_sql_statement(segment, DROP_DATABASE):
        return "SQL DROP DATABASE"

    if should_block_sql_statement(segment, DROP_SCHEMA):
        return "SQL DROP SCHEMA"

    if should_block_sql_statement(segment, TRUNCATE_SQL, util_exclude=TRUNCATE_UTIL):
        return "SQL TRUNCATE"

    if GIT_RESET_HARD.search(segment):
        return "Git hard reset (git reset --hard)"

    if is_git_force_via_config(segment):
        return "Git force push (git -c push.force)"

    if GIT_FORCE_REFSPEC.search(segment):
        return "Git force push (git push +<ref>)"

    if (
        DELETE_FROM.search(segment)
        and not WHERE_CLAUSE.search(segment)
        and should_block_sql_statement(segment, DELETE_FROM)
    ):
        return "SQL DELETE FROM without WHERE clause"

    if DD_DISK.search(segment):
        return "Disk overwrite (dd of=/dev/*)"

    if FORK_BOMB.search(segment):
        return "Fork bomb"

    if MKFS.search(segment):
        return "Filesystem format (mkfs)"

    if DEV_REDIRECT.search(segment):
        return "Raw device overwrite (> /dev/*)"

    if WIPEFS.search(segment):
        return "Disk signature wipe (wipefs)"

    if REMOTE_SHELL.search(segment):
        return "Remote script execution (curl|sh / wget|sh)"

    return None


def check_segment(segment: str) -> str | None:
    for candidate in iter_segment_candidates(segment):
        reason = check_segment_body(candidate)
        if reason:
            return reason
    return None


def check_command(command: str) -> str | None:
    command = normalize_command(command)
    for segment in iter_command_segments(command):
        reason = check_segment(segment)
        if reason:
            return reason
    return None


def main() -> None:
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            sys.exit(0)

        data = json.loads(raw_input)
        if data.get("tool_name") != "Bash":
            sys.exit(0)

        tool_input = data.get("tool_input") or {}
        command = normalize_command(tool_input.get("command") or "")
        if not command:
            sys.exit(0)

        project_path = data.get("cwd") or os.getcwd()
        block_reason = check_command(command)
        if block_reason:
            log_blocked_attempt(command, project_path)
            deny(
                f"{block_reason} blocked. "
                f"Run this command directly in your terminal if you truly need it."
            )
    except Exception:
        # Never block legitimate commands because the hook failed unexpectedly.
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
