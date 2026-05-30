#!/usr/bin/env python3
"""Install the destructive Bash guard into Claude Code hook settings."""

from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path
from typing import Any

HOOK_NAME = "block_destructive_bash.py"


def _load_settings(path: Path) -> dict[str, Any]:
  if not path.exists():
    return {}
  return json.loads(path.read_text(encoding="utf-8"))


def _hook_entry(hook_path: Path) -> dict[str, str]:
  return {"type": "command", "command": str(hook_path)}


def _install_hook_settings(settings: dict[str, Any], hook_path: Path) -> dict[str, Any]:
  hooks = settings.setdefault("hooks", {})
  pre_tool_use = hooks.setdefault("PreToolUse", [])
  if not isinstance(pre_tool_use, list):
    raise ValueError("settings.hooks.PreToolUse must be a list")

  entry = {"matcher": "Bash", "hooks": [_hook_entry(hook_path)]}
  command = str(hook_path)
  for existing in pre_tool_use:
    if not isinstance(existing, dict):
      continue
    if existing.get("matcher") != "Bash":
      continue
    existing_hooks = existing.setdefault("hooks", [])
    if not isinstance(existing_hooks, list):
      continue
    if not any(isinstance(item, dict) and item.get("command") == command for item in existing_hooks):
      existing_hooks.append(_hook_entry(hook_path))
    return settings

  pre_tool_use.append(entry)
  return settings


def main() -> int:
  source = Path(__file__).with_name(HOOK_NAME)
  claude_dir = Path.home() / ".claude"
  hooks_dir = claude_dir / "hooks"
  settings_path = claude_dir / "settings.json"
  target = hooks_dir / HOOK_NAME

  hooks_dir.mkdir(parents=True, exist_ok=True)
  shutil.copy2(source, target)
  target.chmod(target.stat().st_mode | stat.S_IXUSR)

  settings = _load_settings(settings_path)
  settings = _install_hook_settings(settings, target)
  settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

  print(f"Installed {target}")
  print(f"Updated {settings_path}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
