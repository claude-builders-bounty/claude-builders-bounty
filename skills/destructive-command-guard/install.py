#!/usr/bin/env python3
"""Install the destructive command guard into a Claude Code project."""

import json
import os
import shutil
import stat
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def main() -> None:
    project = Path(sys.argv[1] if len(sys.argv) > 1 else os.getcwd()).resolve()
    source_dir = Path(__file__).resolve().parent
    hook_dir = project / ".claude" / "hooks"
    hook_path = hook_dir / "destructive-command-guard.py"
    settings_path = project / ".claude" / "settings.json"

    hook_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_dir / "guard.py", hook_path)
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR)

    settings = load_json(settings_path)
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    group = None
    for candidate in pre_tool_use:
        if candidate.get("matcher") == "Bash":
            group = candidate
            break
    if group is None:
        group = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(group)

    command = "${CLAUDE_PROJECT_DIR}/.claude/hooks/destructive-command-guard.py"
    if not any(hook.get("command") == command for hook in group.setdefault("hooks", [])):
        group["hooks"].append({"type": "command", "command": command})

    write_json(settings_path, settings)
    print(f"Installed destructive command guard in {project}")


if __name__ == "__main__":
    main()
