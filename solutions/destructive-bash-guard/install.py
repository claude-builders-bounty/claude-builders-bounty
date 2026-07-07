import os
import json

settings_path = os.path.expanduser("~/.claude/settings.json")
os.makedirs(os.path.dirname(settings_path), exist_ok=True)

if os.path.exists(settings_path):
    try:
        with open(settings_path, 'r') as f:
            data = json.load(f)
    except Exception:
        data = {}
else:
    data = {}

hooks = data.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])

# Avoid duplicate registration
hook_cmd = os.path.expanduser("~/.claude/hooks/pre-tool-use.py")
already_registered = False

for h in pre_tool_use:
    if h.get("matcher") == "Bash":
        for sub_h in h.get("hooks", []):
            if sub_h.get("command") == hook_cmd:
                already_registered = True
                break

if not already_registered:
    pre_tool_use.append({
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": hook_cmd,
                "timeout": 30,
                "statusMessage": "Verifying command safety..."
            }
        ]
    })
    
with open(settings_path, 'w') as f:
    json.dump(data, f, indent=2)

print("PreToolUse hook registered successfully in ~/.claude/settings.json")
