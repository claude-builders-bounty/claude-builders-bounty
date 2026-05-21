#!/usr/bin/env python3
"""
Installer script for the Claude Code Bash Safety Hook.
Copies the hook script to ~/.claude/hooks/ and registers it in ~/.claude/settings.json.
"""

import os
import shutil
import json
import sys

def main():
    # Define paths
    source_hook = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pre_tool_use_hook.py")
    
    if not os.path.exists(source_hook):
        print(f"Error: Source hook script not found at {source_hook}", file=sys.stderr)
        sys.exit(1)
        
    claude_dir = os.path.expanduser("~/.claude")
    hooks_dir = os.path.join(claude_dir, "hooks")
    target_hook = os.path.join(hooks_dir, "pre_tool_use_hook.py")
    settings_file = os.path.join(claude_dir, "settings.json")
    
    print(f"Creating hooks directory at: {hooks_dir}")
    os.makedirs(hooks_dir, exist_ok=True)
    
    print(f"Copying {source_hook} -> {target_hook}")
    shutil.copy2(source_hook, target_hook)
    
    # Make the script executable
    print("Making the hook executable...")
    os.chmod(target_hook, 0o755)
    
    # Load or initialize settings.json
    settings = {}
    if os.path.exists(settings_file):
        print(f"Reading existing settings from: {settings_file}")
        try:
            with open(settings_file, "r") as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print("Warning: settings.json could not be parsed as valid JSON. Initializing a new configuration.")
        except Exception as e:
            print(f"Warning: Failed to read settings.json: {e}")
            
    # Ensure hooks structure exists
    hooks_config = settings.setdefault("hooks", {})
    pre_tool_use_list = hooks_config.setdefault("PreToolUse", [])
    
    # Define the new hook configuration
    new_hook = {
        "type": "command",
        "command": target_hook,
        "timeout": 60000,
        "statusMessage": "Checking command safety..."
    }
    
    # Look for a matcher for "Bash" or search for existing entry
    bash_matcher_found = False
    for item in pre_tool_use_list:
        if item.get("matcher") == "Bash":
            bash_matcher_found = True
            hooks_under_matcher = item.setdefault("hooks", [])
            # Check if this command is already registered
            already_registered = False
            for h in hooks_under_matcher:
                if h.get("type") == "command" and h.get("command") == target_hook:
                    already_registered = True
                    # Update timeout and status message if needed
                    h["timeout"] = 60000
                    h["statusMessage"] = "Checking command safety..."
                    break
            if not already_registered:
                print("Registering hook in existing Bash matcher list.")
                hooks_under_matcher.append(new_hook)
            else:
                print("Hook is already registered in the Bash matcher list.")
            break
            
    if not bash_matcher_found:
        print("Creating new Bash matcher list and registering hook.")
        pre_tool_use_list.append({
            "matcher": "Bash",
            "hooks": [new_hook]
        })
        
    # Write back settings.json
    print(f"Writing updated settings to: {settings_file}")
    try:
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
        print("Success! Claude Code pre-tool-use hook successfully installed.")
    except Exception as e:
        print(f"Error: Failed to write to {settings_file}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
