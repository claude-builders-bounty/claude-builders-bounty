#!/usr/bin/env python3
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


HOOK_FILE_NAME = "destructive_bash_guard.py"
LOG_FILE_NAME = "blocked.log"


def normalize_command(command):
    return re.sub(r"\s+", " ", command.strip())


def delete_without_where(command):
    for match in re.finditer(r"\bdelete\s+from\b([^;]*)", command, flags=re.IGNORECASE):
        statement_tail = match.group(1)
        if not re.search(r"\bwhere\b", statement_tail, flags=re.IGNORECASE):
            return True
    return False


def block_reason(command):
    normalized = normalize_command(command)
    lowered = normalized.lower()

    if re.search(r"(^|[\s;&|])rm\s+-(?:[a-z]*r[a-z]*f[a-z]*|[a-z]*f[a-z]*r[a-z]*)\b", lowered):
        return "Blocked because recursive forced deletion with rm -rf/rm -fr is destructive."
    if re.search(r"\bdrop\s+table\b", normalized, flags=re.IGNORECASE):
        return "Blocked because DROP TABLE can permanently remove database schema and data."
    if re.search(r"\bgit\s+push\b.*\s(--force|-f)\b", normalized, flags=re.IGNORECASE):
        return "Blocked because force-pushing can overwrite remote history."
    if re.search(r"\btruncate\b", normalized, flags=re.IGNORECASE):
        return "Blocked because TRUNCATE can remove all rows from a table."
    if delete_without_where(normalized):
        return "Blocked because DELETE FROM without a WHERE clause can remove all table rows."

    return ""


def hook_dir():
    return Path.home() / ".claude" / "hooks"


def log_blocked_attempt(command, project_path, reason):
    directory = hook_dir()
    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / LOG_FILE_NAME
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def extract_command(payload):
    tool_input = payload.get("tool_input") or {}
    return tool_input.get("command") or tool_input.get("cmd") or ""


def extract_project_path(payload):
    tool_input = payload.get("tool_input") or {}
    return payload.get("cwd") or payload.get("project_path") or tool_input.get("cwd") or os.getcwd()


def is_bash_tool(payload):
    tool_name = str(payload.get("tool_name") or "").lower()
    return tool_name in {"bash", "shell", "shell_command"}


def run_hook():
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    if not is_bash_tool(payload):
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    reason = block_reason(command)
    if not reason:
        return 0

    project_path = extract_project_path(payload)
    log_blocked_attempt(command, project_path, reason)
    print(f"Command blocked by destructive-bash-guard: {reason}", file=sys.stderr)
    print(f"Attempted command: {command}", file=sys.stderr)
    print("Review the command and choose a safer, narrower operation.", file=sys.stderr)
    return 2


def load_settings(settings_path):
    if not settings_path.exists():
        return {}
    try:
        with settings_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        backup_path = settings_path.with_suffix(".json.bak")
        shutil.copy2(settings_path, backup_path)
        return {}


def install_hook():
    directory = hook_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / HOOK_FILE_NAME
    shutil.copy2(Path(__file__).resolve(), target)

    settings_path = Path.home() / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings = load_settings(settings_path)
    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])
    command = f"{sys.executable} {target}"
    hook_entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }

    existing = json.dumps(pre_tool, sort_keys=True)
    if command not in existing:
        pre_tool.append(hook_entry)

    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    print(f"Installed hook at {target}")
    print(f"Updated settings at {settings_path}")
    return 0


def main():
    if "--install" in sys.argv:
        return install_hook()
    return run_hook()


if __name__ == "__main__":
    raise SystemExit(main())
