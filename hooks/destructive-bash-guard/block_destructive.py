#!/usr/bin/env python3
"""
Destructive Bash Guard - Pre-tool-use hook for Claude Code.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

HOOKS_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = HOOKS_DIR / "blocked.log"
PATTERNS_FILE = Path(__file__).parent / "patterns.yaml"

DEFAULT_PATTERNS = [
    {"name": "rm-rf-root-or-home", "regex": r"\brm\s+(?:-[a-zA-Z]*[rR][fF]|-[a-zA-Z]*[fF][rR]|-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive|-rf|-fr)\s+([/~][^\s]*|~|\*|\.\./?[^\s]*)", "severity": "critical", "description": "Recursive force removal targeting root, home, parent dirs, or wildcards"},
    {"name": "rm-rf-any", "regex": r"\brm\s+(?:-[a-zA-Z]*[rR][fF]|-[a-zA-Z]*[fF][rR]|-rf|-fr)\s+(\*|[/~][^\s]*|\.\./?[^\s]*)", "severity": "critical", "description": "Recursive force removal of root paths, parent dirs, or wildcards"},
    {"name": "mkfs-filesystem", "regex": r"\bmkfs(\.[a-z0-9]+)?\s+", "severity": "critical", "description": "Creating a filesystem wipes the target device"},
    {"name": "dd-write", "regex": r"\bdd\s+.*\bof=/dev/(sd|hd|nvme|xvd|vd|mmcblk)", "severity": "critical", "description": "dd writing to a block device wipes the disk"},
    {"name": "chmod-777", "regex": r"\bchmod\s+(-[a-zA-Z]*R[a-zA-Z]*\s+)?777\s+", "severity": "high", "description": "chmod 777 makes files world-writable (security risk)"},
    {"name": "chown-everyone", "regex": r"\bchown\s+(-[a-zA-Z]*R[a-zA-Z]*\s+)?[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+\s+\/(etc|var|usr|bin|sbin)", "severity": "high", "description": "Changing ownership of system directories"},
    {"name": "drop-table", "regex": r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|MATERIALIZED\s+VIEW)\b", "severity": "critical", "description": "SQL DROP statement destroys schema/data"},
    {"name": "truncate-table", "regex": r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z_][a-zA-Z0-9_.]*", "severity": "critical", "description": "SQL TRUNCATE removes all rows without logging"},
    {"name": "delete-from-no-where-line", "regex": r"\bDELETE\s+FROM\s+[a-zA-Z_][a-zA-Z0-9_.]*\s*;", "severity": "critical", "description": "DELETE FROM without WHERE clause (line-level)"},
    {"name": "git-push-force-protected", "regex": r"\bgit\s+push\s+.*(--force|--force-with-lease|-f)\b.*\b(origin|upstream)\s+(main|master|prod|production|release|stable)\b", "severity": "critical", "description": "Force push to protected branch (main/master/prod)"},
    {"name": "git-push-force-any", "regex": r"\bgit\s+push\s+.*?(--force\b(?!-with-lease)|-f\b(?!-))", "severity": "high", "description": "Force push (--force/-f) overwrites remote history"},
    {"name": "git-reset-hard", "regex": r"\bgit\s+reset\s+--hard\b", "severity": "high", "description": "git reset --hard discards uncommitted changes"},
    {"name": "git-clean-fd", "regex": r"\bgit\s+clean\s+(-[a-zA-Z]*[fF][dD]|-[a-zA-Z]*[dD][fF]|-fd|-df)\b", "severity": "high", "description": "git clean -fd removes untracked files and directories"},
    {"name": "git-branch-delete-force", "regex": r"\bgit\s+branch\s+(-[a-zA-Z]*[dD]\b.*-[a-zA-Z]*[fF]|-[a-zA-Z]*[fF][dD]|-Df|-fd)\s+", "severity": "medium", "description": "git branch -D/-f force-deletes branch"},
    {"name": "curl-pipe-shell", "regex": r"\b(curl|wget|fetch)\b[^\n|]*\|\s*(sh|bash|zsh|fish|ksh|sudo\s+(sh|bash))\b", "severity": "critical", "description": "Downloaded content piped to shell (curl|sh attack vector)"},
    {"name": "curl-pipe-python", "regex": r"\b(curl|wget)\b[^\n|]*\|\s*python\b", "severity": "high", "description": "Downloaded content piped to python (arbitrary code execution)"},
    {"name": "shutdown-reboot", "regex": r"\b(shutdown|reboot|halt|poweroff|init\s+[06]|systemctl\s+(poweroff|reboot|halt))\b", "severity": "critical", "description": "System shutdown/reboot command"},
    {"name": "fork-bomb", "regex": r":\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:", "severity": "critical", "description": "Classic bash fork bomb"},
    {"name": "wipefs", "regex": r"\bwipefs\s+", "severity": "critical", "description": "wipefs erases filesystem signatures from device"},
    {"name": "shred-device", "regex": r"\bshred\s+.*(/dev/|--force\s+/dev/)", "severity": "critical", "description": "shred overwrites device contents"},
]


def load_patterns() -> list[dict]:
    if not PATTERNS_FILE.exists():
        return DEFAULT_PATTERNS
    try:
        import yaml
        data = yaml.safe_load(PATTERNS_FILE.read_text())
        return data.get("patterns", DEFAULT_PATTERNS)
    except Exception:
        return DEFAULT_PATTERNS


class BlockResult:
    def __init__(self, blocked=False, pattern_name="", reason="", severity="", suggestions=None):
        self.blocked = blocked
        self.pattern_name = pattern_name
        self.reason = reason
        self.severity = severity
        self.suggestions = suggestions or []


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, str):
        return tool_input
    if not isinstance(tool_input, dict):
        return ""
    for k in ("command", "cmd", "bash_command", "script", "shell_command"):
        if k in tool_input and isinstance(tool_input[k], str):
            return tool_input[k]
    return " ".join(str(v) for v in tool_input.values() if isinstance(v, str))


SUGGESTIONS = {
    "rm-rf-root-or-home": ["Use specific paths: rm -rf ./build ./dist", "Move to trash: trash-put <path>"],
    "rm-rf-any": ["Be explicit: rm -rf ./build", "Use git clean: git clean -fdx -- <path>"],
    "mkfs-filesystem": ["Verify target: lsblk", "For images: mkfs.ext4 -d ./rootfs /tmp/image.ext4"],
    "dd-write": ["Verify target: lsblk", "Use safer tools: pv or rsync"],
    "chmod-777": ["Use chmod 755", "For shared dirs: chmod 2775 <dir>"],
    "drop-table": ["Use ALTER TABLE or migrations", "Wrap in transaction: BEGIN; DROP TABLE ...; ROLLBACK;"],
    "truncate-table": ["Use DELETE FROM <table> WHERE ...", "Do it from a SQL client, not Claude"],
    "delete-from-no-where": ["Add WHERE clause", "Wrap in transaction for ROLLBACK"],
    "git-push-force-protected": ["Use non-protected branch", "Coordinate manually for main force push"],
    "git-push-force-any": ["Prefer: git push --force-with-lease", "Or new branch: git push origin HEAD:feature/fix"],
    "git-reset-hard": ["Stash first: git stash", "Use git reset --soft or --mixed"],
    "git-clean-fd": ["Dry run: git clean -fdn", "Limit scope: git clean -fd <path>"],
    "curl-pipe-shell": ["Download first, inspect, then run", "Use package managers (apt, brew, pip)"],
    "shutdown-reboot": ["Use systemctl restart <service>", "Use unattended-upgrade framework"],
}


def check_command(cmd: str, patterns: list[dict]) -> BlockResult:
    if not cmd or not cmd.strip():
        return BlockResult(False)
    cleaned_lines = [line.split("#", 1)[0] for line in cmd.splitlines()]
    cleaned = "\n".join(cleaned_lines)

    for pat in patterns:
        try:
            if re.search(pat["regex"], cleaned, re.IGNORECASE | re.MULTILINE):
                return BlockResult(
                    blocked=True,
                    pattern_name=pat["name"],
                    reason=pat.get("description", pat["name"]),
                    severity=pat.get("severity", "high"),
                    suggestions=SUGGESTIONS.get(pat["name"], []),
                )
        except re.error:
            continue

    # Multi-stage: DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\b", cleaned, re.IGNORECASE):
        if not re.search(r"\bWHERE\b", cleaned, re.IGNORECASE):
            return BlockResult(
                blocked=True,
                pattern_name="delete-from-no-where-multi",
                reason="DELETE FROM statement without WHERE clause would remove ALL rows",
                severity="critical",
                suggestions=[
                    "Add WHERE clause: DELETE FROM users WHERE id = 123;",
                    "If you really mean to delete all rows, use TRUNCATE explicitly (also blocked).",
                ],
            )
    return BlockResult(False)


def log_block(command: str, pattern_name: str, severity: str, project_path: str) -> None:
    try:
        HOOKS_DIR.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        truncated = command if len(command) < 500 else command[:500] + "...(truncated)"
        with LOG_FILE.open("a") as f:
            f.write(f"[{ts}] severity={severity} pattern={pattern_name} project={project_path}\n")
            f.write(f"  command: {truncated}\n")
            f.write(f"  cwd: {os.getcwd()}\n")
            f.write("---\n")
    except Exception as e:
        sys.stderr.write(f"[destructive-guard] log write failed: {e}\n")


def emit_block(result: BlockResult, command: str) -> None:
    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"BLOCKED by destructive-bash-guard: {result.reason}\n"
                f"  Pattern: {result.pattern_name}\n"
                f"  Severity: {result.severity}\n"
                f"  Command: {command[:200]}{'...' if len(command) > 200 else ''}\n"
            ),
        }
    }
    if result.suggestions:
        decision["hookSpecificOutput"]["permissionDecisionReason"] += (
            "\nSuggestions:\n" + "\n".join(f"  - {s}" for s in result.suggestions) + "\n"
        )
    print(json.dumps(decision, indent=2))


def emit_allow() -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
        }
    }))


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            emit_allow()
            return 0
        payload = json.loads(raw)
    except json.JSONDecodeError:
        emit_allow()
        return 0

    if os.environ.get("DESTRUCTIVE_GUARD_OVERRIDE") == "1":
        sys.stderr.write("[destructive-guard] WARNING: override active via DESTRUCTIVE_GUARD_OVERRIDE=1\n")
        emit_allow()
        return 0

    command = extract_command(payload)
    if not command:
        emit_allow()
        return 0

    patterns = load_patterns()
    result = check_command(command, patterns)
    project_path = os.getcwd()

    if result.blocked:
        log_block(command, result.pattern_name, result.severity, project_path)
        emit_block(result, command)
        return 0
    emit_allow()
    return 0


if __name__ == "__main__":
    main()
