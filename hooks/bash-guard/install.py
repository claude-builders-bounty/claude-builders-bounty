"""Install the hook and merge one Bash matcher into the user's settings."""

import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile


def main():
    root = Path.home() / ".claude"
    settings = root / "settings.json"
    config = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    target = root / "hooks" / "bash-guard.py"
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    action = {"type": "command", "command": shlex.join([sys.executable, str(target)])}
    groups = config.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if not any(g.get("matcher") == "Bash" and action in g.get("hooks", []) for g in groups):
        groups.append({"matcher": "Bash", "hooks": [action]})
    shutil.copyfile(Path(__file__).with_name("guard.py"), target)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=root, delete=False) as out:
        json.dump(config, out, indent=2)
        out.write("\n")
    os.replace(out.name, settings)
    print("Installed the Bash guard. Restart Claude Code to load the hook.")


if __name__ == "__main__":
    main()
