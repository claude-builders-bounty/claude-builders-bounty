#!/usr/bin/env bash
# block-destructive-commands.sh
# Claude Code pre-tool-use hook that blocks dangerous bash commands.
# Install: cp block-destructive-commands.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
#
# Bounty: claude-builders-bounty/claude-builders-bounty#3 ($100)

set -euo pipefail

HOOK_INPUT="$(cat)"

CLAUDE_HOOK_INPUT="$HOOK_INPUT" python3 - <<'PY'
import json
import os
import re
import sys
from datetime import datetime


def block(reason: str, command: str, project_path: str) -> None:
    hook_dir = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
    os.makedirs(hook_dir, exist_ok=True)
    log_file = os.path.join(hook_dir, "blocked.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as handle:
        handle.write(
            f"[{timestamp}] BLOCKED | cmd: {command} | reason: {reason} | path: {project_path}\n"
        )

    print(f"BLOCKED: {reason}")
    print(f"Command: {command}")
    print("Run the command in a normal terminal if you intentionally want to bypass the hook.")
    sys.exit(2)


raw = os.environ.get("CLAUDE_HOOK_INPUT", "")
if not raw.strip():
    sys.exit(0)

try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(0)

tool_name = str(payload.get("tool_name") or payload.get("tool") or "").strip().lower()
tool_input = payload.get("tool_input") or {}
command = str(tool_input.get("command") or "").strip()
project_path = (
    str(tool_input.get("workdir") or tool_input.get("cwd") or "").strip()
    or os.getcwd()
)

if tool_name != "bash" or not command:
    sys.exit(0)

normalized = " ".join(command.split())
upper = normalized.upper()

rm_force_recursive = [
    re.compile(r"\brm\b[^;\n|&]*\s-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b"),
    re.compile(r"\brm\b[^;\n|&]*\s-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*\b"),
    re.compile(r"\brm\b[^;\n|&]*\s-[A-Za-z]*r[A-Za-z]*\s-[A-Za-z]*f[A-Za-z]*\b"),
    re.compile(r"\brm\b[^;\n|&]*\s-[A-Za-z]*f[A-Za-z]*\s-[A-Za-z]*r[A-Za-z]*\b"),
]

if any(pattern.search(normalized) for pattern in rm_force_recursive):
    block(
        "rm -rf detected: recursive force deletion is irreversible and can destroy entire directories",
        normalized,
        project_path,
    )

if re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", upper):
    block(
        "DROP TABLE/DATABASE detected: this permanently deletes database structures and all related data",
        normalized,
        project_path,
    )

if re.search(r"\bgit\s+push\b[^;\n|&]*\s(--force(?:-with-lease)?|-f)\b", normalized):
    block(
        "git push --force detected: this can overwrite remote history and destroy other contributors' commits",
        normalized,
        project_path,
    )

if re.search(r"\bTRUNCATE\s+(TABLE\s+)?[A-Z_][A-Z0-9_.$]*\b", upper):
    block(
        "TRUNCATE detected: this empties an entire table without row-level filtering",
        normalized,
        project_path,
    )

for statement in [segment.strip() for segment in re.split(r";|\n", upper) if segment.strip()]:
    if "DELETE FROM" in statement and "WHERE" not in statement:
        block(
            "DELETE FROM without WHERE detected: this deletes every row in the target table",
            normalized,
            project_path,
        )

sys.exit(0)
PY
