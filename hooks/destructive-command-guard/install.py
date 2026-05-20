#!/usr/bin/env python3
"""Install the destructive Bash command guard into Claude Code settings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_settings(settings_path: Path) -> dict[str, Any]:
    if not settings_path.exists():
        return {}
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot update invalid JSON in {settings_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Cannot update {settings_path}: expected a JSON object")
    return data


def main() -> int:
    home = Path.home()
    hooks_dir = home / ".claude" / "hooks"
    hook_path = hooks_dir / "block_destructive_bash.py"
    settings_path = home / ".claude" / "settings.json"

    if not hook_path.exists():
        raise SystemExit(f"Hook script not found at {hook_path}. Run the copy command first.")

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings = _load_settings(settings_path)
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise SystemExit("Cannot update settings: hooks.PreToolUse must be a list")

    command = f"python3 {hook_path}"
    hook_entry = {"type": "command", "command": command}
    matcher_entry = {"matcher": "Bash", "hooks": [hook_entry]}

    already_installed = any(
        isinstance(entry, dict)
        and entry.get("matcher") == "Bash"
        and any(isinstance(hook, dict) and hook.get("command") == command for hook in entry.get("hooks", []))
        for entry in pre_tool_use
    )
    if not already_installed:
        pre_tool_use.append(matcher_entry)

    settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Installed destructive command guard in {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
