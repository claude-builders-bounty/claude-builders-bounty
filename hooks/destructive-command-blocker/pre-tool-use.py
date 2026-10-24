#!/usr/bin/env python3
"""
Claude Code Security Hook: Destructive Bash Command Interceptor
Intercepts dangerous, irreversible operations (rm -rf, git push --force, DROP TABLE, TRUNCATE, DELETE without WHERE)
before tool execution, logging attempts and preventing accidental workspace damage.
"""

import datetime
import json
import os
import re
import sys
from pathlib import Path

# Log file location as specified in requirements: ~/.claude/hooks/blocked.log
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

def is_dangerous_command(command: str):
    """
    Evaluates whether a command matches destructive blacklisted patterns.
    Returns: (is_dangerous: bool, rule_name: str, explanation: str)
    """
    if not command or not isinstance(command, str):
        return False, "", ""
    
    cmd_clean = command.strip()

    # 1. Recursive force removal (rm -rf, rm -fr, rm -r -f, rm --recursive --force)
    if re.search(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)", cmd_clean, re.IGNORECASE) or \
       re.search(r"\brm\s+.*(-r|-R|--recursive)\b.*(-f|--force)\b", cmd_clean, re.IGNORECASE) or \
       re.search(r"\brm\s+.*(-f|--force)\b.*(-r|-R|--recursive)\b", cmd_clean, re.IGNORECASE):
        return True, "rm -rf", "Recursive force directory/file deletion detected."

    # 2. SQL DROP TABLE
    if re.search(r"\bDROP\s+TABLE\b", cmd_clean, re.IGNORECASE):
        return True, "DROP TABLE", "Destructive schema drop table statement detected."

    # 3. Git force push (git push --force, -f, +branch, --force-with-lease)
    if re.search(r"\bgit\s+push\b.*(\s+-f\b|\s+--force\b|\s+--force-with-lease\b|\s+\+[a-zA-Z0-9_\-\./]+)", cmd_clean):
        return True, "git push --force", "Remote git history override (force push) detected."

    # 4. SQL TRUNCATE
    if re.search(r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z0-9_`\"\.]+", cmd_clean, re.IGNORECASE):
        return True, "TRUNCATE", "Destructive table data purge (TRUNCATE) detected."

    # 5. SQL DELETE FROM without WHERE clause
    # Look for DELETE FROM <table> and ensure a WHERE clause follows before statement end
    delete_matches = list(re.finditer(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_`\"\.]+)", cmd_clean, re.IGNORECASE))
    for m in delete_matches:
        start_idx = m.end()
        end_idx = cmd_clean.find(";", start_idx)
        clause = cmd_clean[start_idx:end_idx] if end_idx != -1 else cmd_clean[start_idx:]
        if not re.search(r"\bWHERE\b", clause, re.IGNORECASE):
            table_name = m.group(1)
            return True, "DELETE FROM without WHERE", f"Unbounded database deletion on table '{table_name}' without WHERE constraint."

    return False, "", ""

def log_blocked_attempt(command: str, rule: str, project_dir: str):
    """Appends blocked audit entry to ~/.claude/hooks/blocked.log"""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{now_str}] BLOCKED: rule='{rule}' | project='{project_dir}' | command='{command}'\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"[Hook Warning] Failed to write blocked audit log: {e}\n")

def main():
    raw_input = ""
    command_to_evaluate = ""
    project_dir = os.getcwd()

    # 1. Positional CLI argument has highest priority when testing/invoking directly
    if len(sys.argv) > 1:
        command_to_evaluate = " ".join(sys.argv[1:])

    # 2. Check stdin (Claude Code JSON hook interface)
    if not command_to_evaluate:
        try:
            # Check if stdin is non-empty without blocking
            import select
            rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
            if rlist:
                raw_input = sys.stdin.read()
                if raw_input.strip():
                    try:
                        payload = json.loads(raw_input)
                        if isinstance(payload, dict):
                            tool_name = payload.get("tool", "") or payload.get("tool_name", "")
                            tool_input = payload.get("input", {}) or payload.get("tool_input", {})
                            project_dir = payload.get("project", "") or payload.get("cwd", project_dir)
                            
                            if tool_name and tool_name.lower() not in ["bash", "sh", "terminal"]:
                                sys.exit(0)

                            if isinstance(tool_input, dict):
                                command_to_evaluate = tool_input.get("command", "") or tool_input.get("cmd", "")
                            elif isinstance(tool_input, str):
                                command_to_evaluate = tool_input
                    except json.JSONDecodeError:
                        command_to_evaluate = raw_input.strip()
        except Exception:
            pass

    # 3. Environment variable fallback
    if not command_to_evaluate:
        command_to_evaluate = os.environ.get("CLAUDE_TOOL_COMMAND", "") or os.environ.get("TOOL_COMMAND", "")

    # If no command identified, allow execution
    if not command_to_evaluate:
        sys.exit(0)

    # Evaluate safety
    is_blocked, rule, explanation = is_dangerous_command(command_to_evaluate)

    if is_blocked:
        log_blocked_attempt(command_to_evaluate, rule, project_dir)
        
        # Output clear, structured error message to Claude and user
        error_msg = (
            f"\n🛑 [SECURITY HOOK BLOCKED] Destructive Bash Command Intercepted!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Matched Rule   : {rule}\n"
            f"• Risk Reason    : {explanation}\n"
            f"• Command Blocked: {command_to_evaluate}\n"
            f"• Project Path   : {project_dir}\n"
            f"• Audit Log      : {LOG_PATH}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Execution halted to prevent catastrophic data or repository loss.\n"
            f"If this operation is genuinely intended, please execute it manually outside Claude Code.\n"
        )
        sys.stderr.write(error_msg)
        sys.exit(1)

    # Safe command — allow execution
    sys.exit(0)

if __name__ == "__main__":
    main()
