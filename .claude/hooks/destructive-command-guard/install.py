#!/usr/bin/env python3
import json
import sys
from pathlib import Path


SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def main() -> int:
    hook_path = Path(__file__).with_name("hook.py").resolve()
    command = f'"{sys.executable}" "{hook_path}"'

    settings = _load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    matcher = _find_bash_matcher(pre_tool_use)
    if matcher is None:
        matcher = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(matcher)

    matcher_hooks = matcher.setdefault("hooks", [])
    if not any(hook.get("command") == command for hook in matcher_hooks if isinstance(hook, dict)):
        matcher_hooks.append({"type": "command", "command": command})

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed destructive command guard in {SETTINGS_PATH}")
    return 0


def _load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}

    try:
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup_path = SETTINGS_PATH.with_suffix(".json.bak")
        backup_path.write_text(SETTINGS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        return {}

    return settings if isinstance(settings, dict) else {}


def _find_bash_matcher(pre_tool_use: list) -> dict | None:
    for matcher in pre_tool_use:
        if isinstance(matcher, dict) and matcher.get("matcher") == "Bash":
            return matcher
    return None


if __name__ == "__main__":
    raise SystemExit(main())

