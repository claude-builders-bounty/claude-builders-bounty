#!/usr/bin/env bash
# install.sh — cài hook vào ~/.claude (idempotent, merge settings.json, không ghi đè).
set -uo pipefail
HOOK_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOK_DIR"
cp ./block-dangerous.sh "$HOOK_DIR/block-dangerous.sh"
chmod +x "$HOOK_DIR/block-dangerous.sh"
chmod 700 "$HOOK_DIR"
python3 - "$HOOK_DIR" <<'EOF'
import json, os, sys
hook_dir = sys.argv[1]
p = os.path.expanduser("~/.claude/settings.json")
cfg = {}
if os.path.exists(p):
    cfg = json.loads(open(p).read() or "{}")
entry = {"matcher": "Bash", "hooks": [{"type": "command",
        "command": os.path.join(hook_dir, "block-dangerous.sh")}]}
hooks = cfg.setdefault("hooks", {}).setdefault("PreToolUse", [])
if not any(e.get("matcher") == "Bash" and
           "block-dangerous.sh" in json.dumps(e.get("hooks", [])) for e in hooks):
    hooks.append(entry)
open(p, "w").write(json.dumps(cfg, indent=2))
print("settings.json merged (giữ nguyên config cũ)")
EOF
echo "xong: hook tại $HOOK_DIR/block-dangerous.sh"
