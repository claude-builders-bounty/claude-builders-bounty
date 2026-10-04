#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS="${HOME}/.claude/settings.json"
mkdir -p "$HOOK_DIR"
install -m 755 "$ROOT/block_destructive.py" "$HOOK_DIR/block_destructive.py"
export ROOT
python3 <<'PY'
import json
import os
from pathlib import Path

settings = Path(os.environ["HOME"]) / ".claude" / "settings.json"
fragment = json.loads(
    Path(os.environ["ROOT"]).joinpath("settings.fragment.json").read_text()
)
if settings.exists():
    data = json.loads(settings.read_text() or "{}")
else:
    data = {}
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = fragment["hooks"]["PreToolUse"][0]
if not any(
    h.get("matcher") == "Bash"
    and any(
        x.get("command", "").endswith("block_destructive.py")
        for x in h.get("hooks", [])
    )
    for h in pre
):
    pre.append(entry)
settings.parent.mkdir(parents=True, exist_ok=True)
settings.write_text(json.dumps(data, indent=2) + "\n")
print(f"Installed hook and updated {settings}")
PY
