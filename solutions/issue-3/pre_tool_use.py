#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Dangerous Bash Commands

This hook intercepts and blocks dangerous bash commands before they are executed
by Claude Code, preventing accidental data loss or system damage.

Installation:
  1. Copy this file to ~/.claude/hooks/pre_tool_use.py
  2. Make it executable: chmod +x ~/.claude/hooks/pre_tool_use.py
  3. Claude Code will automatically invoke it before executing bash commands

Author: disillusi0n
Bounty: $100 (Issue #3)
"""

import sys
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Dangerous command patterns
DANGEROUS_PATTERNS = {
    "rm -rf": {
        "pattern": r"\brm\s+(-[rf]+\s+|--recursive\s+|--force\s+)+",
        "reason": "Recursive force deletion can cause irreversible data loss",
        "severity": "HIGH"
    },
    "DROP TABLE": {
        "pattern": r"\bDROP\s+TABLE\b",
        "reason": "SQL DROP TABLE will permanently delete database tables",
        "severity": "HIGH"
    },
    "TRUNCATE": {
        "pattern": r"\bTRUNCATE\s+(TABLE\s+)?",
        "reason": "TRUNCATE will permanently delete all data in a table",
        "severity": "HIGH"
    },
    "DELETE FROM": {
        "pattern": r"\bDELETE\s+FROM\b.*\b(WHERE|;)\b",
        "reason": "DELETE FROM without proper WHERE clause can delete all data",
        "severity": "HIGH"
    },
    "git push --force": {
        "pattern": r"\bgit\s+push\s+.*(--force|-f)\b",
        "reason": "Force push can overwrite remote history and cause data loss",
        "severity": "MEDIUM"
    },
    "DROP DATABASE": {
        "pattern": r"\bDROP\s+(DATABASE|SCHEMA)\b",
        "reason": "DROP DATABASE will permanently delete entire databases",
        "severity": "HIGH"
    },
}

def check_command(command: str) -> Tuple[bool, List[Dict]]:
    """
    Check if a command contains dangerous patterns.
    
    Returns:
        (is_safe, violations): Tuple of safety status and list of violations
    """
    violations = []
    command_upper = command.upper()
    
    for name, config in DANGEROUS_PATTERNS.items():
        pattern = config["pattern"]
        if re.search(pattern, command, re.IGNORECASE):
            violations.append({
                "name": name,
                "pattern": pattern,
                "reason": config["reason"],
                "severity": config["severity"],
                "matched_text": re.search(pattern, command, re.IGNORECASE).group(0)
            })
    
    is_safe = len(violations) == 0
    return is_safe, violations

def log_blocked_attempt(command: str, violations: List[Dict], project_path: str = ""):
    """Log blocked attempt to file."""
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path,
        "violations": violations
    }
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

def main():
    """
    Main hook entry point.
    
    Claude Code will call this script with JSON input via stdin containing:
    - tool: The tool being invoked (e.g., "bash")
    - input: The command/input to the tool
    - context: Additional context (optional)
    """
    try:
        # Read input from Claude Code
        input_data = json.load(sys.stdin)
        
        tool = input_data.get("tool", "")
        command = input_data.get("input", "")
        project_path = input_data.get("context", {}).get("project_path", "")
        
        # Only check bash commands
        if tool != "bash":
            # Allow non-bash tools
            output = {
                "action": "allow",
                "message": ""
            }
            print(json.dumps(output))
            sys.exit(0)
        
        # Check command for dangerous patterns
        is_safe, violations = check_command(command)
        
        if is_safe:
            # Allow the command
            output = {
                "action": "allow",
                "message": ""
            }
            print(json.dumps(output))
            sys.exit(0)
        else:
            # Block the command
            log_blocked_attempt(command, violations, project_path)
            
            # Build error message
            error_parts = ["⚠️  BLOCKED: Dangerous command detected!\n"]
            error_parts.append(f"Command: {command}\n\n")
            error_parts.append("Violations:\n")
            
            for v in violations:
                error_parts.append(f"  ❌ {v['name']}: {v['reason']}\n")
                error_parts.append(f"     Matched: '{v['matched_text']}'\n")
                error_parts.append(f"     Severity: {v['severity']}\n")
            
            error_parts.append(f"\nThis attempt has been logged to: {LOG_FILE}")
            
            error_message = "".join(error_parts)
            
            output = {
                "action": "block",
                "message": error_message
            }
            
            print(json.dumps(output))
            sys.exit(0)
    
    except Exception as e:
        # On error, allow the command (fail open for safety)
        output = {
            "action": "allow",
            "message": f"Hook error (allowing command): {str(e)}"
        }
        print(json.dumps(output))
        sys.exit(0)

if __name__ == "__main__":
    main()
