import os
import shutil
import json
import sys

def main():
    home = os.path.expanduser("~")
    claude_dir = os.path.join(home, ".claude")
    hooks_dir = os.path.join(claude_dir, "hooks")
    
    os.makedirs(hooks_dir, exist_ok=True)
    
    # Copy script to hooks directory
    src_script = "pre-tool-use.py"
    dest_script = os.path.join(hooks_dir, "pre-tool-use.py")
    
    shutil.copy2(src_script, dest_script)
    os.chmod(dest_script, 0o755)
    print(f"Copied hook script to {dest_script}")
    
    # Configure settings.json
    settings_file = os.path.join(claude_dir, "settings.json")
    settings = {}
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            pass
            
    if "hooks" not in settings:
        settings["hooks"] = {}
        
    hook_entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": f"python \"{dest_script}\"",
                "timeout": 5000,
                "statusMessage": "Running security checks..."
            }
        ]
    }
    
    settings["hooks"]["PreToolUse"] = [hook_entry]
    
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        
    print(f"Successfully configured hooks in {settings_file}")
    print("\nInstallation successful! Pre-tool-use hook is active.")

if __name__ == "__main__":
    main()
