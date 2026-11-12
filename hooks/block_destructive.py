#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
Prevents accidental execution of dangerous commands:
- rm -rf / rm -fr / recursive force deletion
- DROP TABLE
- git push --force / git push -f
- TRUNCATE / TRUNCATE TABLE
- DELETE FROM without a WHERE clause
"""
import sys
import re
import os
import json
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    # rm -rf, rm -fr, rm -r -f, rm -f -r, rm -R -f, rm --recursive --force, rm -rfv, etc.
    (
        r'\brm\s+(?:-[a-zA-Z0-9_-]*\s+)*(?:(?:-[a-zA-Z0-9]*[rR][a-zA-Z0-9]*[fF][a-zA-Z0-9]*|-[a-zA-Z0-9]*[fF][a-zA-Z0-9]*[rR][a-zA-Z0-9]*)|(?:--recursive\s+.*--force|--force\s+.*--recursive)|(?:-[rR]\s+.*-[fF]|-[fF]\s+.*-[rR]))\b',
        "Recursive force file deletion (`rm -rf` / `rm -fr`) is prohibited by safety policy."
    ),
    # DROP TABLE
    (
        r'\bDROP\s+TABLE(?:\s+IF\s+EXISTS)?\s+["`\w.]+',
        "Dropping database tables (`DROP TABLE`) is prohibited by safety policy."
    ),
    # git push --force, -f, --force-with-lease
    (
        r'\bgit\s+push\b.*(?:\s+--force\b|\s+-f\b|\s+--force-with-lease\b)',
        "Force-pushing git branches (`git push --force` / `-f`) is prohibited by safety policy."
    ),
    # TRUNCATE [TABLE]
    (
        r'\bTRUNCATE(?:\s+TABLE)?\s+["`\w.]+',
        "Truncating database tables (`TRUNCATE`) is prohibited by safety policy."
    ),
    # DELETE FROM without WHERE
    (
        r'\bDELETE\s+FROM\s+["`\w.]+(?:\s*;|\s*$|\s+(?!WHERE\b)[\w\s;`"\'\(\)=<>!]+$)',
        "Deleting database records without a WHERE clause (`DELETE FROM table`) is prohibited by safety policy."
    ),
]

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")


def evaluate_command(command: str) -> tuple[bool, str]:
    """
    Evaluates whether a bash command contains dangerous or destructive patterns.
    Returns (is_allowed, reason).
    """
    if not command or not command.strip():
        return True, "Empty command"

    # Normalize newlines and extra spaces for evaluation
    clean_cmd = re.sub(r'\s+', ' ', command).strip()

    # Special check for DELETE FROM with WHERE clause
    if re.search(r'\bDELETE\s+FROM\b', clean_cmd, re.IGNORECASE):
        if re.search(r'\bDELETE\s+FROM\b.*\bWHERE\b', clean_cmd, re.IGNORECASE | re.DOTALL):
            # Has a WHERE clause, check other patterns
            pass
        else:
            return False, "Deleting database records without an explicit `WHERE` clause (`DELETE FROM ...`) is prohibited by safety policy."

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, clean_cmd, re.IGNORECASE):
            return False, reason

    return True, "Allowed"


def log_blocked(command: str, project_path: str, reason: str, log_path: str = LOG_FILE) -> None:
    """
    Logs blocked execution attempts with timestamp, project path, reason, and command.
    """
    target_dir = os.path.dirname(log_path)
    os.makedirs(target_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = f"[{timestamp}] PROJECT={project_path} REASON={reason} ATTEMPTED_COMMAND={command}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)


def extract_command_and_cwd() -> tuple[str, str]:
    """
    Extracts the tool command and current working directory from stdin JSON or CLI arguments.
    Compatible with Claude Code hook protocols and direct CLI testing.
    """
    command = ""
    project_path = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read().strip()
            if raw_input:
                try:
                    payload = json.loads(raw_input)
                    if isinstance(payload, dict):
                        # Claude Code pre-tool-use payload format
                        input_block = payload.get("input", {})
                        command = (
                            input_block.get("command")
                            or payload.get("command")
                            or ""
                        )
                        project_path = (
                            payload.get("context", {}).get("project_dir")
                            or payload.get("cwd")
                            or payload.get("project_path")
                            or project_path
                        )
                    else:
                        command = str(payload)
                except json.JSONDecodeError:
                    command = raw_input
        except Exception:
            pass

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    return command.strip(), project_path


def main() -> int:
    command, project_path = extract_command_and_cwd()

    if not command:
        return 0

    is_allowed, reason = evaluate_command(command)

    if not is_allowed:
        log_blocked(command, project_path, reason)
        sys.stderr.write("\n" + "=" * 60 + "\n")
        sys.stderr.write("🛑 [BLOCKED BY CLAUDE CODE PRE-TOOL-USE HOOK]\n")
        sys.stderr.write("=" * 60 + "\n")
        sys.stderr.write(f"Reason: {reason}\n")
        sys.stderr.write(f"Attempted Command: {command}\n")
        sys.stderr.write(f"Project Path: {project_path}\n")
        sys.stderr.write(f"Audit Log: {LOG_FILE}\n")
        sys.stderr.write("=" * 60 + "\n\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
