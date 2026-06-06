#!/usr/bin/env python3
"""Install the dangerous Bash blocker into the user's Claude Code config."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


def _settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def _hooks_dir() -> Path:
    return Path.home() / ".claude" / "hooks"


def _hook_target() -> Path:
    return _hooks_dir() / "block_dangerous_bash.py"


def _load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Existing settings file is not valid JSON: {path}") from exc


def _write_settings(path: Path, settings: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _ensure_hook(settings: dict, python_exe: str, hook_path: Path) -> dict:
    hooks = settings.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])

    matcher = None
    for entry in pre:
        if entry.get("matcher") == "Bash":
            matcher = entry
            break

    hook_entry = {
        "type": "command",
        "command": python_exe,
        "args": [str(hook_path)],
        "timeout": 10,
    }

    if matcher is None:
        pre.append({"matcher": "Bash", "hooks": [hook_entry]})
        return settings

    existing_hooks = matcher.setdefault("hooks", [])
    filtered = []
    for item in existing_hooks:
        if item.get("type") == "command" and item.get("command") == python_exe and item.get("args") == [str(hook_path)]:
            continue
        filtered.append(item)
    filtered.append(hook_entry)
    matcher["hooks"] = filtered
    return settings


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    source_hook = repo_root / "block_dangerous_bash.py"
    if not source_hook.exists():
        raise SystemExit(f"Missing hook source: {source_hook}")

    hooks_dir = _hooks_dir()
    hooks_dir.mkdir(parents=True, exist_ok=True)
    target_hook = _hook_target()
    shutil.copy2(source_hook, target_hook)

    settings = _load_settings(_settings_path())
    settings = _ensure_hook(settings, sys.executable, target_hook)
    _write_settings(_settings_path(), settings)

    print(f"Installed hook to {target_hook}")
    print(f"Updated settings at {_settings_path()}")
    print("Installation complete. Claude Code will now block the specified dangerous Bash commands.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
