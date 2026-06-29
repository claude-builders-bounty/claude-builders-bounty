#!/usr/bin/env python3
import os
import json
import urllib.request
import sys
import shutil

HOOKS_DIR = os.path.expanduser('~/.claude/hooks')
HOOK_PATH = os.path.join(HOOKS_DIR, 'pre-tool-use')
SETTINGS_PATH = os.path.expanduser('~/.claude/settings.json')

print("Installing Pre-Tool-Use Safety Hook...")

# 1. Create hooks directory
os.makedirs(HOOKS_DIR, exist_ok=True)

# 2. Copy locally if in repo, otherwise download from GitHub
local_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hooks', 'pre_tool_use.py')
if os.path.exists(local_src):
    try:
        shutil.copy(local_src, HOOK_PATH)
        os.chmod(HOOK_PATH, 0o755)
        print(f"✓ Installed hook locally to {HOOK_PATH}")
    except Exception as e:
        print(f"Error copying hook script: {e}")
        sys.exit(1)
else:
    url = "https://raw.githubusercontent.com/aashu91/claude-builders-bounty/main/hooks/pre_tool_use.py"
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
        with open(HOOK_PATH, 'wb') as f:
            f.write(content)
        os.chmod(HOOK_PATH, 0o755)
        print(f"✓ Downloaded hook to {HOOK_PATH}")
    except Exception as e:
        print(f"Error downloading hook script: {e}")
        sys.exit(1)

# 3. Configure settings.json
settings = {}
if os.path.exists(SETTINGS_PATH):
    try:
        with open(SETTINGS_PATH, 'r') as f:
            settings = json.load(f)
    except Exception:
        pass

# Initialize nested keys if not present
if 'hooks' not in settings:
    settings['hooks'] = {}
if 'PreToolUse' not in settings['hooks']:
    settings['hooks']['PreToolUse'] = []

# Check if our hook is already registered
registered = False
for entry in settings['hooks']['PreToolUse']:
    if entry.get('matcher') == 'Bash':
        for h in entry.get('hooks', []):
            if 'pre-tool-use' in h.get('command', ''):
                registered = True
                break

if not registered:
    # Add registration
    settings['hooks']['PreToolUse'].append({
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": HOOK_PATH
            }
        ]
    })
    try:
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"✓ Registered hook in {SETTINGS_PATH}")
    except Exception as e:
        print(f"Error updating settings.json: {e}")
        sys.exit(1)
else:
    print("✓ Hook is already registered in settings.json")

print("\n🎉 Installation successful! Claude Code will now block destructive commands.")
