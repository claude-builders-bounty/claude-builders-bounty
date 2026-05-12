#!/usr/bin/env python3
"""Install the destructive Bash command blocker into Claude Code settings."""

from __future__ import annotations

import json
import shutil
import shlex
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOOK = REPO_ROOT / "hooks" / "block_destructive_bash.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
TARGET_HOOK = HOOKS_DIR / "block_destructive_bash.py"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"


def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def install_hook_file() -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, TARGET_HOOK)


def merge_hook_settings(settings: dict) -> dict:
    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(TARGET_HOOK))}"
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    bash_matcher = None
    for matcher in pre_tool_use:
        if matcher.get("matcher") == "Bash":
            bash_matcher = matcher
            break

    if bash_matcher is None:
        bash_matcher = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(bash_matcher)

    matcher_hooks = bash_matcher.setdefault("hooks", [])
    hook_config = {"type": "command", "command": command}
    if hook_config not in matcher_hooks:
        matcher_hooks.append(hook_config)

    return settings


def save_settings(settings: dict) -> None:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    install_hook_file()
    settings = merge_hook_settings(load_settings())
    save_settings(settings)
    print(f"Installed hook at {TARGET_HOOK}")
    print(f"Updated settings at {SETTINGS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
