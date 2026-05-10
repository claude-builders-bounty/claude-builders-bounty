#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook — Destructive Command Protection

Blocks dangerous bash commands before execution and logs all attempts.
Installed to ~/.claude/hooks/pre-tool-use/

Hook Format:
  - Receives tool_use JSON on stdin
  - Returns modified tool_use JSON on stdout
  - Returning empty {} blocks the tool call
"""

import json, sys, os, re
from datetime import datetime

# ── Dangerous patterns ──────────────────────────────────────────
# These are blocked when they appear as the primary tool command
DESTRUCTIVE_PATTERNS = {
    # File system destruction
    "rm -rf /": "⚠️ Blocked: `rm -rf /` would destroy the root filesystem",
    "rm -rf /*": "⚠️ Blocked: Recursive deletion of root is never intentional",
    "rm -rf ~": "⚠️ Blocked: Recursive deletion of home directory is unsafe",
    "rm -rf $HOME": "⚠️ Blocked: Recursive deletion of home directory is unsafe",
    "rm -rf --no-preserve-root": "⚠️ Blocked: Forced root deletion is never allowed",
    
    # Git force push (destructive to history)
    "git push --force": "⚠️ Blocked: Force push rewrites remote history. Use `git push --force-with-lease` instead",
    "git push -f": "⚠️ Blocked: Force push rewrites remote history. Use `git push --force-with-lease` instead",
    "git push origin +": "⚠️ Blocked: Force push via refspec. Use `--force-with-lease` instead",
    
    # Database destruction
    "DROP TABLE": "⚠️ Blocked: `DROP TABLE` permanently deletes database tables",
    "DROP DATABASE": "⚠️ Blocked: `DROP DATABASE` permanently deletes the database",
    "TRUNCATE": "⚠️ Blocked: `TRUNCATE` removes all rows from a table without backup",
    "DELETE FROM": "⚠️ Blocked: Unconditional `DELETE FROM` without WHERE clause (use `DELETE FROM ... WHERE ...`)",
    "DROP SCHEMA": "⚠️ Blocked: `DROP SCHEMA` permanently deletes a schema",
    "DROP OWNED": "⚠️ Blocked: `DROP OWNED` permanently removes database objects",

    # System operations
    "mkfs.": "⚠️ Blocked: Formatting a filesystem would destroy all data on the device",
    "dd if=/dev/zero": "⚠️ Blocked: Writing zeros to a device would destroy all data",
    "dd if=/dev/urandom": "⚠️ Blocked: Writing random data to a device would destroy all data",
    "shutdown": "⚠️ Blocked: Shutting down the system is outside the scope of code generation",
    "reboot": "⚠️ Blocked: Rebooting the system is outside the scope of code generation",
    "poweroff": "⚠️ Blocked: Powering off the system is outside the scope of code generation",
    "halt": "⚠️ Blocked: Halting the system is outside the scope of code generation",
    "init 0": "⚠️ Blocked: Shutdown command is outside the scope of code generation",
    "init 6": "⚠️ Blocked: Reboot command is outside the scope of code generation",
    
    # Permission/ownership changes
    "chmod -R 777": "⚠️ Blocked: Making everything world-writable is a security risk",
    "chmod 777 /": "⚠️ Blocked: Making root world-writable breaks system security",
    "chown -R": "⚠️ Blocked: Recursive ownership changes may break system permissions",
    
    # Package manager mass operations (risky)
    "pip uninstall -y": "⚠️ Blocked: Mass package uninstall may break Python environment",
    "npm uninstall -g": "⚠️ Blocked: Global package uninstall may break Node.js tooling",
    "apt remove": "⚠️ Blocked: Removing system packages may break dependencies",
    "apt purge": "⚠️ Blocked: Purging system packages is irreversible",
    "dpkg --purge": "⚠️ Blocked: Purging packages may brick the system",
    
    # Network manipulation
    "iptables -F": "⚠️ Blocked: Flushing iptables rules will break firewall",
    "ufw disable": "⚠️ Blocked: Disabling the firewall creates a security hole",
    "ufw reset": "⚠️ Blocked: Resetting firewall rules will drop all protections",
}

# Check if command contains any destructive pattern
def is_dangerous(command: str) -> tuple[bool, str]:
    """Returns (is_dangerous, reason_message)"""
    cmd_lower = command.lower().strip()
    
    for pattern, message in DESTRUCTIVE_PATTERNS.items():
        if pattern.lower() in cmd_lower:
            return True, message
    
    # Smart checks: DELETE FROM without WHERE
    if re.search(r'\bdelete\s+from\b', cmd_lower, re.IGNORECASE):
        # Check if there's a WHERE clause AFTER the DELETE FROM
        # Simple heuristic: if DELETE FROM exists but WHERE doesn't appear after it
        delete_match = re.search(r'\bdelete\s+from\b', cmd_lower, re.IGNORECASE)
        if delete_match:
            rest = cmd_lower[delete_match.end():]
            if 'where' not in rest and 'limit' not in rest:
                # But allow if it's clearly a SQL file being created
                if 'echo' not in cmd_lower and 'cat <<' not in cmd_lower and "'" not in cmd_lower:
                    return True, "⚠️ Blocked: Unconditional `DELETE FROM` without a WHERE clause"
    
    # rm -rf without explicit path safety
    if re.search(r'\brm\s+-rf?\b', cmd_lower):
        # Check if it's operating on a known safe path
        if any(safe in cmd_lower for safe in ['/tmp/', 'node_modules', '.git/', 'dist', 'build', '.next', '.venv']):
            return False, ""
        # If rm -rf with just a generic name, let through (might be project-specific)
        return False, ""
    
    return False, ""

def log_blocked(command: str, reason: str, project_path: str = ""):
    """Log blocked attempts to ~/.claude/hooks/blocked.log"""
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] BLOCKED | project: {project_path} | cmd: {command[:200]} | reason: {reason}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)
    
    # Keep log manageable — max 1000 lines
    with open(log_file, "r") as f:
        lines = f.readlines()
    if len(lines) > 1000:
        with open(log_file, "w") as f:
            f.writelines(lines[-500:])

def main():
    """Main hook handler: reads tool_use from stdin, returns modified or blocked."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({}))  # No op
            return
        
        tool_use = json.loads(raw)
        command = tool_use.get("command", "") if isinstance(tool_use, dict) else ""
        
        if not command:
            print(raw.strip())
            return
        
        is_danger, reason = is_dangerous(command)
        
        if is_danger:
            # Get project context
            project_path = os.getcwd()
            
            # Log the blocked attempt
            log_blocked(command, reason, project_path)
            
            # Block the tool call
            print(json.dumps({}))
            sys.stderr.write(f"\n{reason}\n")
            sys.stderr.flush()
        else:
            # Pass through
            print(raw.strip())
    
    except json.JSONDecodeError:
        print(json.dumps({}))
    except Exception as e:
        # Never crash Claude — log and pass through
        print(raw.strip() if 'raw' in dir() else json.dumps({}))
        sys.stderr.write(f"\n[pre-tool-use hook error] {e}\n")

if __name__ == "__main__":
    main()
