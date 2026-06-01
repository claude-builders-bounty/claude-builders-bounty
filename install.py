import os
import sys
import shutil
import json

def main():
    print("Installing Claude Code Destructive Bash Blocker Hook...")
    
    # 1. Paths
    home_dir = os.path.expanduser("~")
    hooks_dir = os.path.join(home_dir, ".claude", "hooks")
    settings_path = os.path.join(home_dir, ".claude", "settings.json")
    
    os.makedirs(hooks_dir, exist_ok=True)
    
    # 2. Copy the hook script to ~/.claude/hooks/
    src_hook = "pre_tool_use_hook.py"
    dest_hook = os.path.join(hooks_dir, "pre_tool_use_hook.py")
    
    if not os.path.exists(src_hook):
        # If run from another directory, locate it relatively
        src_hook = os.path.join(os.path.dirname(__file__), "pre_tool_use_hook.py")
        
    shutil.copy(src_hook, dest_hook)
    print(f"Copied hook engine to: {dest_hook}")
    
    # 3. Create the executable bash wrapper script
    wrapper_path = os.path.join(hooks_dir, "pre-tool-use")
    with open(wrapper_path, "w", newline="\n") as f:
        f.write("#!/usr/bin/env bash\n")
        f.write('if command -v python3 &>/dev/null; then\n')
        f.write('  python3 "$HOME/.claude/hooks/pre_tool_use_hook.py"\n')
        f.write('else\n')
        f.write('  python "$HOME/.claude/hooks/pre_tool_use_hook.py"\n')
        f.write('fi\n')
    
    # Make wrapper executable
    try:
        os.chmod(wrapper_path, 0o755)
    except:
        pass
    print(f"Created executable hook wrapper at: {wrapper_path}")

    # 4. Configure ~/.claude/settings.json
    settings_data = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings_data = json.load(f)
        except Exception:
            settings_data = {}
            
    # Add hook entry to settings JSON
    if "hooks" not in settings_data:
        settings_data["hooks"] = {}
        
    # Standard format for PreToolUse hooks
    hook_entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": f"bash {home_dir.replace('\\', '/')}/.claude/hooks/pre-tool-use",
                "timeout": 5000
            }
        ]
    }
    
    if "PreToolUse" not in settings_data["hooks"]:
        settings_data["hooks"]["PreToolUse"] = []
        
    # Check if hook already registered to avoid duplication
    exists = False
    for entry in settings_data["hooks"]["PreToolUse"]:
        if entry.get("matcher") == "Bash":
            exists = True
            # Overwrite hooks list with ours
            entry["hooks"] = hook_entry["hooks"]
            break
            
    if not exists:
        settings_data["hooks"]["PreToolUse"].append(hook_entry)
        
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings_data, f, indent=2)
        
    print(f"Configured settings at: {settings_path}")
    print("\nSUCCESS: Installation complete! The destructive command blocker hook is active.")

if __name__ == "__main__":
    main()
