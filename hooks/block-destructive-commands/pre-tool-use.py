#!/usr/bin/env python3
"""Claude Code PreToolUse hook — blocks destructive bash commands.

Detects destructive patterns in bare commands, chained segments (; && ||),
pipeline stages, shell -c wrappers (including bash --login -c, bash -l -c,
bash -lc, env bash -lc, bash $'...' and $"..." quoting), and container
exec/run invocations
(docker/podman/kubectl/nerdctl exec|run, compose exec|run, and compose exec|run).
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
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
# Match shell -c after optional flags (bash --login -c) or combined short flags (bash -lc).
SHELL_C = re.compile(
    r"\b(?:sh|bash|zsh|dash)\b"
    r"(?:\s+(?:--(?!--)[\w-]+(?:=\S+)?|-[A-Za-z]+))*"
    r"\s+-[A-Za-z]*c\b\s+",
    re.IGNORECASE,
)
INTERPRETER_INLINE = re.compile(
    r"\b(?:python3?|ruby|perl|node)\s+(?:-[a-zA-Z]+\s+)*-[ec]\s+(?:'([^']*)'|\"((?:\\.|[^\"\\])*)\"|(\S+))",
    re.IGNORECASE,
)
INTERPRETER_EXECUTION_HINT = re.compile(
    r"\b(?:system|exec(?:vp|ve|le)?|spawn|popen|subprocess|os\.system|child_process)\b",
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
CONTAINER_RUNTIME_INVOCATION = re.compile(
    r"\b(?:docker(?:\s+compose|-compose)?|podman(?:\s+compose|-compose)?|kubectl(?:\s+compose|-compose)?|nerdctl(?:\s+compose|-compose)?|compose)\s+(?:exec|run)\b",
    re.IGNORECASE,
)
# Unicode Cf (format) chars can split rm/-rf tokens and bypass regex checks.
_INVISIBLE_FORMAT_CHARS = re.compile(
    r"[\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]"
)
# Hangul/braille filler glyphs (Lo/other) used like zero-width chars to split tokens.
# U+115F/U+1160 (Hangul choseong/jungseong), U+3164 (Hangul filler), U+FFA0 (halfwidth), U+2800 (braille blank).
_FILLER_CODEPOINTS = ("\u115f", "\u1160", "\u3164", "\uffa0", "\u2800")
_INVISIBLE_FILLER_CHARS = re.compile("[" + "".join(_FILLER_CODEPOINTS) + "]")


def _has_filler_glyphs(text: str) -> bool:
    """True when Hangul/braille filler codepoints appear in text."""
    return any(filler in text for filler in _FILLER_CODEPOINTS)


def strip_invisible_format_chars(text: str, *, replacement: str = "") -> str:
    """Remove or space-replace Unicode Cf/Mn chars and filler glyphs that split tokens."""
    has_category_chars = any(
        unicodedata.category(ch) in {"Cf", "Mn"} for ch in text
    )
    if not has_category_chars and not _has_filler_glyphs(text):
        return text
    stripped = "".join(
        replacement if unicodedata.category(ch) in {"Cf", "Mn"} else ch
        for ch in text
    )
    return _INVISIBLE_FILLER_CHARS.sub(replacement, stripped)


_BASH_ANSI_C_ESCAPES = {
    "a": "\a",
    "b": "\b",
    "e": "\x1b",
    "E": "\x1b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
    "\\": "\\",
    "'": "'",
    '"': '"',
    "?": "?",
}

CONTAINER_NAME = re.compile(r"^(?:[^\s\"']+|\"[^\"]*\"|'[^']*')\s*")
CONTAINER_EXEC_BOOL_SHORT_FLAGS = frozenset("itTd")
# Long flags that never take a separate value token (e.g. --rm, not --workdir).
CONTAINER_EXEC_BOOL_LONG_FLAGS = frozenset(
    {
        "rm",
        "detach",
        "interactive",
        "tty",
        "privileged",
        "read-only",
        "init",
        "stdin",
        "sig-proxy",
        "help",
        "quiet",
    }
)


def command_has_invisible_chars(command: str) -> bool:
    """True when null bytes or invisible Unicode may split pattern tokens."""
    if "\x00" in command:
        return True
    if _INVISIBLE_FORMAT_CHARS.search(command) is not None:
        return True
    if _has_filler_glyphs(command):
        return True
    return command != strip_invisible_format_chars(command)


def normalize_command(command: str, *, invisible_replacement: str = "") -> str:
    """Strip padding and neutralize null/invisible bytes that split regex tokens."""
    normalized = command.strip()
    if not command_has_invisible_chars(normalized):
        return normalized
    normalized = normalized.replace("\x00", "")
    normalized = strip_invisible_format_chars(
        normalized, replacement=invisible_replacement
    )
    return re.sub(r" +", " ", normalized).strip()


def normalized_command_variants(command: str) -> list[str]:
    """Return compact and space-expanded normalizations for invisible-char evasion."""
    stripped = command.strip()
    if not stripped:
        return [""]
    if not command_has_invisible_chars(stripped):
        return [stripped]
    variants: list[str] = []
    for replacement in ("", " "):
        normalized = normalize_command(stripped, invisible_replacement=replacement)
        if normalized not in variants:
            variants.append(normalized)
    return variants


def iter_command_segments(command: str) -> list[str]:
    """Split chained bash commands so each segment is checked independently."""
    segments: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    escape = False
    index = 0
    length = len(command)

    def flush() -> None:
        segment = "".join(current).strip()
        if segment:
            segments.append(segment)
        current.clear()

    while index < length:
        char = command[index]
        if escape:
            current.append(char)
            escape = False
            index += 1
            continue
        if char == "\\" and in_double:
            current.append(char)
            escape = True
            index += 1
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            current.append(char)
            index += 1
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            current.append(char)
            index += 1
            continue
        if not in_single and not in_double:
            if command.startswith("&&", index):
                flush()
                index += 2
                continue
            if command.startswith("||", index):
                flush()
                index += 2
                continue
            if char == ";":
                flush()
                index += 1
                continue
        current.append(char)
        index += 1

    flush()
    return segments


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


# Whitelist wrapper flags so rm/git short options (e.g. -rf) are never peeled as sudo/env flags.
# sudo accepts UID shorthand -u#0 (same as -u root) without a separating space.
_SUDO_UID_SHORTHAND = r"-u#\d+"
_SUDO_VALUE_FLAGS = rf"(?:{_SUDO_UID_SHORTHAND}|(?:-(?:u|g|p|C|D|R|t|U)\s+\S+))"
_SUDO_BOOL_FLAGS = r"-(?:A|b|B|E|e|h|H|i|K|k|l|L|n|P|S|s|V|v)"
_SUDO_FLAGS = (
    rf"(?:{_SUDO_VALUE_FLAGS}|{_SUDO_BOOL_FLAGS}|--[\w-]+(?:=\S+|\s+\S+)?|\w+=\S*|--)"
)
_DOAS_VALUE_FLAGS = r"-(?:u)\s+\S+"
_DOAS_BOOL_FLAGS = r"-(?:L|n|s)"
_DOAS_FLAGS = (
    rf"(?:{_DOAS_VALUE_FLAGS}|{_DOAS_BOOL_FLAGS}|--[\w-]+(?:=\S+|\s+\S+)?|--)"
)
_PKEXEC_FLAGS = r"(?:--user(?:=\S+|\s+\S+)|--[\w-]+(?:=\S+|\s+\S+)?|--)"
# runuser -c takes the rest of the line as the command (handled by extract_runuser_c_inner).
_RUNUSER_VALUE_FLAGS = r"-(?:u|g|G|s|w|l)\s+\S+"
_RUNUSER_BOOL_FLAGS = r"-(?:P)"
_RUNUSER_FLAGS = (
    rf"(?:{_RUNUSER_VALUE_FLAGS}|{_RUNUSER_BOOL_FLAGS}|--[\w-]+(?:=\S+|\s+\S+)?|--)"
)
_ENV_VALUE_FLAGS = r"-(?:u)\s+\S+"
_ENV_BOOL_FLAGS = r"-(?:i|0)"
_ENV_FLAGS = (
    rf"(?:{_ENV_VALUE_FLAGS}|{_ENV_BOOL_FLAGS}|--[\w-]+(?:=\S+|\s+\S+)?|\w+=\S*|--)"
)
_COMMAND_BOOL_FLAGS = r"-(?:p|V|v|E|F)"
_COMMAND_FLAGS = (
    rf"(?:{_COMMAND_BOOL_FLAGS}|--[\w-]+(?:=\S+|\s+\S+)?|--)"
)
_COMMAND_WRAPPER = re.compile(
    r"^(?:"
    rf"sudo(?:\s+{_SUDO_FLAGS})*\s+|"
    rf"doas(?:\s+{_DOAS_FLAGS})*\s+|"
    rf"pkexec(?:\s+{_PKEXEC_FLAGS})*\s+|"
    rf"runuser(?:\s+{_RUNUSER_FLAGS})*\s+|"
    rf"env(?:\s+{_ENV_FLAGS})*\s+|"
    rf"command(?:\s+{_COMMAND_FLAGS})*\s+"
    r")+",
    re.IGNORECASE,
)


def extract_runuser_c_inner(segment: str) -> str | None:
    """Return the command payload from ``runuser`` ``-c`` (rest of line after ``-c``)."""
    stripped = segment.strip()
    if not re.match(r"^runuser\b", stripped, re.IGNORECASE):
        return None
    match = re.search(r"\s-c\s+", stripped, re.IGNORECASE)
    if not match:
        return None
    inner = stripped[match.end() :].strip()
    return inner or None


def unwrap_command_wrapper(segment: str) -> str:
    """Peel sudo/doas/pkexec/runuser/env/command prefixes before pattern checks."""
    stripped = segment.strip()
    unwrapped = _COMMAND_WRAPPER.sub("", stripped).strip()
    return unwrapped or stripped


def stripped_segment(segment: str) -> str:
    """Remove leading sudo/env prefixes so bare SQL statements are detectable."""
    stripped = unwrap_command_wrapper(segment)
    stripped = re.sub(r"^(\w+=\S*\s+)+", "", stripped)
    return stripped


def extract_interpreter_inline_inner(segment: str) -> str | None:
    """Return the -e/-c payload from python/ruby/perl/node one-liners."""
    match = INTERPRETER_INLINE.search(segment)
    if not match:
        return None
    return next(group for group in match.groups() if group is not None)


def parse_shell_c_argument(payload: str) -> str | None:
    """Parse the argument token after sh/bash -c (quotes, $'...', $\"...\", or bare word)."""
    text = payload.lstrip()
    if not text:
        return None
    if text.startswith('$"'):
        end = 2
        escape = False
        while end < len(text):
            char = text[end]
            if escape:
                escape = False
                end += 1
                continue
            if char == "\\":
                escape = True
                end += 1
                continue
            if char == '"':
                return text[2:end]
            end += 1
        return None
    if text.startswith("$'"):
        index = 2
        length = len(text)
        while index < length:
            char = text[index]
            if char == "'":
                literal = text[: index + 1]
                decoded = decode_bash_ansi_c_quoting(literal)
                return decoded if decoded is not None else literal[2:-1]
            if char == "\\" and index + 1 < length:
                index += 2
                continue
            index += 1
        return None
    if text[0] == "'":
        end = 1
        while end < len(text):
            if text[end] == "'":
                return text[1:end]
            end += 1
        return None
    if text[0] == '"':
        end = 1
        escape = False
        while end < len(text):
            char = text[end]
            if escape:
                escape = False
                end += 1
                continue
            if char == "\\":
                escape = True
                end += 1
                continue
            if char == '"':
                return text[1:end]
            end += 1
        return None
    match = re.match(r"\S+", text)
    return match.group(0) if match else None


def decode_bash_ansi_c_quoting(literal: str) -> str | None:
    """Decode bash $'...' tokens so \\x20-style escapes cannot hide destructive commands."""
    if not (literal.startswith("$'") and literal.endswith("'") and len(literal) >= 3):
        return None
    body = literal[2:-1]
    out: list[str] = []
    index = 0
    length = len(body)
    while index < length:
        char = body[index]
        if char != "\\":
            out.append(char)
            index += 1
            continue
        index += 1
        if index >= length:
            out.append("\\")
            break
        esc = body[index]
        index += 1
        if esc == "x" and index + 1 < length:
            hex_digits = body[index : index + 2]
            if len(hex_digits) == 2 and all(
                ch in "0123456789abcdefABCDEF" for ch in hex_digits
            ):
                out.append(chr(int(hex_digits, 16)))
                index += 2
                continue
        if esc == "u" and index + 3 < length:
            hex_digits = body[index : index + 4]
            if all(ch in "0123456789abcdefABCDEF" for ch in hex_digits):
                out.append(chr(int(hex_digits, 16)))
                index += 4
                continue
        if esc == "U" and index + 7 < length:
            hex_digits = body[index : index + 8]
            if all(ch in "0123456789abcdefABCDEF" for ch in hex_digits):
                out.append(chr(int(hex_digits, 16)))
                index += 8
                continue
        if esc in "01234567":
            oct_digits = esc
            while (
                len(oct_digits) < 3
                and index < length
                and body[index] in "01234567"
            ):
                oct_digits += body[index]
                index += 1
            out.append(chr(int(oct_digits, 8) & 0xFF))
            continue
        out.append(_BASH_ANSI_C_ESCAPES.get(esc, esc))
    return "".join(out)


def extract_shell_c_inner(segment: str) -> str | None:
    """Return decoded shell -c payload (handles $'...' ANSI-C quoting)."""
    match = SHELL_C.search(segment)
    if not match:
        return None
    return parse_shell_c_argument(segment[match.end() :])


def embedded_shell_sql(segment: str, pattern: re.Pattern[str]) -> bool:
    """True when a shell -c wrapper embeds a matching SQL statement."""
    inner = extract_shell_c_inner(segment)
    if inner is None:
        return False
    return bool(pattern.search(inner))


def embedded_interpreter_sql(segment: str, pattern: re.Pattern[str]) -> bool:
    """True when an interpreter -e/-c wrapper embeds a matching SQL statement."""
    inner = extract_interpreter_inline_inner(segment)
    if inner is None:
        return False
    if not INTERPRETER_EXECUTION_HINT.search(inner):
        return False
    return bool(pattern.search(inner))


def iter_pipe_stages(segment: str) -> list[str]:
    """Split pipeline stages so rm -rf after a display tool is still detected."""
    return [stage.strip() for stage in segment.split("|") if stage.strip()]


def _consume_container_exec_flags(tail: str) -> str:
    """Strip exec option flags; stop at ``--`` separator or the next positional token."""
    while tail:
        if tail.startswith("-- "):
            return tail[3:].strip()
        if flag_match := re.match(r"--[\w-]+=\S+\s*", tail):
            tail = tail[flag_match.end() :].strip()
            continue
        if flag_match := re.match(r"--([\w-]+)\s+", tail):
            flag_name = flag_match.group(1).lower()
            tail = tail[flag_match.end() :].strip()
            if (
                flag_name not in CONTAINER_EXEC_BOOL_LONG_FLAGS
                and tail
                and not tail.startswith("-")
            ):
                value_match = re.match(r"\S+\s*", tail)
                if value_match:
                    tail = tail[value_match.end() :].strip()
            continue
        if flag_match := re.match(r"-\w+\s+", tail):
            flag_chars = flag_match.group().strip()[1:]
            tail = tail[flag_match.end() :].strip()
            if (
                len(flag_chars) == 1
                and flag_chars not in CONTAINER_EXEC_BOOL_SHORT_FLAGS
                and tail
                and not tail.startswith("-")
            ):
                value_match = re.match(r"\S+\s*", tail)
                if value_match:
                    tail = tail[value_match.end() :].strip()
            continue
        break
    return tail


def extract_container_exec_inner(segment: str) -> str | None:
    """Return the command run inside docker/podman/kubectl/nerdctl exec or compose run."""
    match = CONTAINER_RUNTIME_INVOCATION.search(segment)
    if not match:
        return None
    tail = _consume_container_exec_flags(segment[match.end() :].strip())
    if not tail:
        return None
    name_match = CONTAINER_NAME.match(tail)
    if not name_match:
        return None
    inner = _consume_container_exec_flags(tail[name_match.end() :].strip())
    return inner or None


def iter_segment_candidates(segment: str) -> list[str]:
    """When exec wraps a command, check only the extracted inner payload."""
    inner = extract_container_exec_inner(segment)
    if inner is not None:
        return [inner]
    return [segment]


def segment_has_rm_rf_invocation(segment: str) -> bool:
    """Block rm -rf only when rm is executed, not when echoed or searched."""
    inner = extract_shell_c_inner(segment)
    if inner is not None:
        for sub in iter_command_segments(inner):
            if segment_has_rm_rf_invocation(sub):
                return True
        return False
    inner = extract_interpreter_inline_inner(segment)
    if inner is not None and INTERPRETER_EXECUTION_HINT.search(inner):
        for sub in iter_command_segments(inner):
            if segment_has_rm_rf_invocation(sub):
                return True
        return False
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
    if util_exclude and util_exclude.search(segment):
        return False
    if embedded_shell_sql(segment, pattern):
        return True
    if embedded_interpreter_sql(segment, pattern):
        return True
    if not pattern.search(segment):
        return False
    if SQL_CLIENT.search(segment):
        return True
    if NON_SQL_TOOLS.match(segment):
        return False
    return bool(pattern.match(stripped_segment(segment)))


# GNU rm accepts --recursive/--force with optional =VALUE (e.g. --recursive=always).
_RM_RECURSIVE_FLAG = re.compile(
    r"(?:--recursive(?:=|\b)|(?:^|\s)-[A-Za-z]*r[A-Za-z]*\b)",
    re.IGNORECASE,
)
_RM_FORCE_FLAG = re.compile(
    r"(?:--force(?:=|\b)|(?:^|\s)-[A-Za-z]*f[A-Za-z]*\b)",
    re.IGNORECASE,
)


def is_rm_rf(command: str) -> bool:
    """True when rm uses both recursive (-r/--recursive) and force (-f/--force) flags.

    Matches GNU long options in any order, including ``--recursive=always`` and
    ``--force=once``, combined short flags (``-rf``), and mixed short/long forms.
    """
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


def segment_has_delete_from_without_where(segment: str) -> bool:
    """True when DELETE FROM appears without WHERE in raw or decoded shell -c text."""
    texts = [segment]
    inner = extract_shell_c_inner(segment)
    if inner is not None:
        texts.append(inner)
    return any(
        DELETE_FROM.search(text) and not WHERE_CLAUSE.search(text) for text in texts
    )


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
        segment_has_delete_from_without_where(segment)
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
    runuser_inner = extract_runuser_c_inner(segment)
    if runuser_inner is not None:
        reason = check_segment_body(runuser_inner)
        if reason:
            return reason
    segment = unwrap_command_wrapper(segment)
    for candidate in iter_segment_candidates(segment):
        reason = check_segment_body(candidate)
        if reason:
            return reason
    return None


def check_command(command: str) -> str | None:
    for normalized in normalized_command_variants(command):
        for segment in iter_command_segments(normalized):
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
        raw_command = tool_input.get("command") or ""
        command = raw_command.strip()
        if not command:
            sys.exit(0)

        project_path = data.get("cwd") or os.getcwd()
        block_reason = check_command(command)
        if block_reason:
            log_blocked_attempt(raw_command.strip(), project_path)
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
