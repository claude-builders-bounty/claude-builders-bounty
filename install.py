#!/usr/bin/env python3
"""
Cross-Platform Installer for Claude Code PreToolUse Destructive Command Guard.
Installs the safety hook into ~/.claude/hooks/ and safely merges the hook
into ~/.claude/settings.json without clobbering existing configuration.
"""

import json
import os
import shutil
import sys
from pathlib import Path

def install():
    home = Path.home()
    claude_dir = home / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_file = claude_dir / "settings.json"
    
    # 1. Create target directories
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Copy hook files
    src_dir = Path(__file__).resolve().parent / "hooks"
    py_hook_src = src_dir / "pre_tool_use_safety.py"
    sh_hook_src = src_dir / "block_destructive.sh"
    
    py_hook_dst = hooks_dir / "pre_tool_use_safety.py"
    sh_hook_dst = hooks_dir / "block_destructive.sh"
    
    if py_hook_src.exists():
        shutil.copy2(py_hook_src, py_hook_dst)
        py_hook_dst.chmod(0o755)
        print(f"✓ Copied Python hook to: {py_hook_dst}")
        
    if sh_hook_src.exists():
        shutil.copy2(sh_hook_src, sh_hook_dst)
        sh_hook_dst.chmod(0o755)
        print(f"✓ Copied Bash hook to: {sh_hook_dst}")
        
    # 3. Read and non-destructively merge settings.json
    settings = {}
    if settings_file.exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception as e:
            print(f"! Warning: Failed to parse existing settings.json ({e}). Starting fresh.")
            settings = {}
            
    # Ensure hooks structure exists
    if "hooks" not in settings or not isinstance(settings["hooks"], dict):
        settings["hooks"] = {}
        
    if "PreToolUse" not in settings["hooks"] or not isinstance(settings["hooks"]["PreToolUse"], list):
        settings["hooks"]["PreToolUse"] = []
        
    hook_cmd = f"python {py_hook_dst}" if sys.platform == "win32" else str(py_hook_dst)
    
    # Check if hook already registered
    already_registered = False
    for item in settings["hooks"]["PreToolUse"]:
        if isinstance(item, dict) and item.get("matcher") == "Bash":
            hooks_list = item.get("hooks", [])
            for h in hooks_list:
                if isinstance(h, dict) and "pre_tool_use_safety" in h.get("command", ""):
                    already_registered = True
                    break
                    
    if not already_registered:
        # Check if there's already a Bash matcher entry to merge into
        bash_entry = None
        for item in settings["hooks"]["PreToolUse"]:
            if isinstance(item, dict) and item.get("matcher") == "Bash":
                bash_entry = item
                break
                
        new_hook_def = {
            "type": "command",
            "command": hook_cmd
        }
        
        if bash_entry is not None:
            if "hooks" not in bash_entry or not isinstance(bash_entry["hooks"], list):
                bash_entry["hooks"] = []
            bash_entry["hooks"].append(new_hook_def)
        else:
            settings["hooks"]["PreToolUse"].append({
                "matcher": "Bash",
                "hooks": [new_hook_def]
            })
            
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        print(f"✓ Successfully registered hook in: {settings_file}")
    else:
        print(f"ℹ Hook was already registered in: {settings_file}")
        
    print("\n🎉 PreToolUse safety guard successfully installed and activated!")

if __name__ == "__main__":
    install()
