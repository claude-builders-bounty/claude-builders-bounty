#!/usr/bin/env python3
import json
import sys
import re
import os
from datetime import datetime

# Configuration
HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOKS_DIR, "blocked.log")
CONFIG_FILE = os.path.join(HOOKS_DIR, "blocker_config.json")

# Ensure hooks directory exists
os.makedirs(HOOKS_DIR, exist_ok=True)

# Default Banned Patterns
BANNED_PATTERNS = [
    # File System
    {
        "regex": r"rm\s+-(?:r|f|rf|fr)\s+.*(?:/|\*|\.\.|~|bin|boot|dev|etc|home|lib|lib64|proc|root|run|sbin|sys|usr|var)",
        "message": "Destructive 'rm' command targeting system or root directories.",
        "suggestion": "Use 'trash' or 'rm -i' for individual files, and never target system directories."
    },
    {
        "regex": r"chmod\s+-R\s+(?:777|666)\s+/",
        "message": "Recursive permissive chmod on root.",
        "suggestion": "Only change permissions on specific project files using restrictive modes (e.g., 644 or 755)."
    },
    # Databases (SQL) - Simple heuristic for destructive actions without WHERE
    {
        "regex": r"(?:DROP|TRUNCATE)\s+(?:TABLE|DATABASE|SCHEMA)",
        "message": "Direct table or database deletion.",
        "suggestion": "Verify the schema and use migrations or specific management tools instead."
    },
    {
        "regex": r"DELETE\s+FROM\s+\w+\b(?!.*\bWHERE\b)",
        "message": "DELETE statement without a WHERE clause.",
        "suggestion": "Always include a WHERE clause or use a transaction: BEGIN; DELETE ...; COMMIT;"
    },
    {
        "regex": r"UPDATE\s+\w+\s+SET\s+.*?(?!.*\bWHERE\b)",
        "message": "UPDATE statement without a WHERE clause.",
        "suggestion": "Always include a WHERE clause to avoid updating all rows."
    },
    # Git
    {
        "regex": r"git\s+push\s+.*--(?:force|f)(?!\w)",
        "message": "Forced git push detected.",
        "suggestion": "Use 'git push --force-with-lease' to avoid overwriting others' work."
    },
    {
        "regex": r"git\s+branch\s+-(?:D)\s+",
        "message": "Forced branch deletion.",
        "suggestion": "Use 'git branch -d' to ensure the branch is merged before deletion."
    },
    # DevOps
    {
        "regex": r"docker\s+(?:rm|rmi)\s+-(?:f|rf).*(?:\$\(|`|all|--all)",
        "message": "Mass deletion of Docker resources.",
        "suggestion": "List resources first and delete them selectively by ID or name."
    },
    {
        "regex": r"kubectl\s+delete\s+.*(?:--all|all|ns\s+)",
        "message": "Mass deletion of Kubernetes resources or namespaces.",
        "suggestion": "Target specific resources by name and avoid global deletions."
    }
]

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"whitelist": [], "custom_patterns": []}

def log_blocked(command, message, project_path):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "reason": message,
        "project_path": project_path
    }
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def main():
    # Read input from stdin
    try:
        input_data = json.load(sys.stdin)
    except Exception as e:
        # If not JSON, we might be called in a different way, but for Claude Code it should be JSON
        return

    if input_data.get("tool_name") != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    project_path = os.getcwd()
    
    config = load_config()
    
    # Check whitelist
    for allowed in config.get("whitelist", []):
        if re.search(allowed, command):
            sys.exit(0)

    # Check patterns
    patterns = BANNED_PATTERNS + config.get("custom_patterns", [])
    
    for p in patterns:
        if re.search(p["regex"], command, re.IGNORECASE | re.MULTILINE | re.DOTALL):
            msg = p["message"]
            sug = p.get("suggestion", "Review the command for potential destructive side effects.")
            
            full_error = f"\n🛑 [BLOCKER] Destructive Command Intercepted\nReason: {msg}\nSuggestion: {sug}\n"
            print(full_error, file=sys.stderr)
            
            log_blocked(command, msg, project_path)
            sys.exit(2) # Exit code 2 blocks the tool call in Claude Code

    sys.exit(0)

if __name__ == "__main__":
    main()
