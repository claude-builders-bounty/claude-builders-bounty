#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path


def install_settings(target: str, settings_path: str) -> None:
    path = Path(settings_path)
    settings: dict[str, object] = {}
    if path.exists():
        settings = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(settings, dict):
            raise SystemExit(f"{path} must contain a JSON object")

    hooks = settings.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise SystemExit(f"{path} has an invalid hooks setting")

    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        raise SystemExit(f"{path} has an invalid PreToolUse setting")

    for matcher in pre_tool_use:
        if not isinstance(matcher, dict):
            continue
        configured_hooks = matcher.get("hooks", [])
        if isinstance(configured_hooks, list) and any(
            hook.get("command") == target
            for hook in configured_hooks
            if isinstance(hook, dict)
        ):
            break
    else:
        pre_tool_use.append(
            {
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": target}],
            }
        )

    print(json.dumps(settings, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    install_settings(sys.argv[1], sys.argv[2])
