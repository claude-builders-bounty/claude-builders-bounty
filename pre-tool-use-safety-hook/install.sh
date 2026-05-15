#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
claude_dir="${HOME}/.claude"
hooks_dir="${claude_dir}/hooks"
settings_path="${claude_dir}/settings.json"

mkdir -p "${hooks_dir}"
cp "${script_dir}/.claude/hooks/block-destructive-bash.py" "${hooks_dir}/block-destructive-bash.py"
chmod +x "${hooks_dir}/block-destructive-bash.py"

python3 - "${settings_path}" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
command = "python3 ~/.claude/hooks/block-destructive-bash.py"
entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": command}],
}

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Refusing to edit invalid JSON in {settings_path}: {exc}")
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])

already_installed = any(
    item.get("matcher") == "Bash"
    and any(hook.get("command") == command for hook in item.get("hooks", []))
    for item in pre_tool_use
    if isinstance(item, dict)
)

if not already_installed:
    pre_tool_use.append(entry)

settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
print(f"Installed destructive Bash blocker in {settings_path}")
PY
