from __future__ import annotations

import json
import shutil
from pathlib import Path


HOOK_NAME = "block_destructive.py"


def main() -> int:
    repo_dir = Path(__file__).resolve().parent
    hook_dir = Path.home() / ".claude" / "hooks"
    settings_path = Path.home() / ".claude" / "settings.json"
    hook_dir.mkdir(parents=True, exist_ok=True)
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    target_hook = hook_dir / HOOK_NAME
    shutil.copyfile(repo_dir / HOOK_NAME, target_hook)
    settings = load_settings(settings_path)
    settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": "python",
                "args": [str(target_hook)],
            }
        ],
    }
    if not has_entry(settings["hooks"]["PreToolUse"], target_hook):
        settings["hooks"]["PreToolUse"].append(entry)
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(f"Installed hook at {target_hook}")
    print(f"Updated settings at {settings_path}")
    return 0


def load_settings(settings_path: Path) -> dict:
    if not settings_path.exists():
        return {}
    try:
        parsed = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = settings_path.with_suffix(".json.bak")
        shutil.copyfile(settings_path, backup)
        print(f"Existing settings were invalid JSON. Backed up to {backup}")
        return {}
    return parsed if isinstance(parsed, dict) else {}


def has_entry(entries: list, target_hook: Path) -> bool:
    target = str(target_hook)
    for entry in entries:
        for hook in entry.get("hooks", []):
            if target in hook.get("args", []) or target in hook.get("command", ""):
                return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
