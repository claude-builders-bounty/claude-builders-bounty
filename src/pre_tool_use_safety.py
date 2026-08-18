#!/usr/bin/env python3
import sys
import os
import json
import re
from datetime import datetime

BLOCKED_PATTERNS = [
    (r'\brm\s+.*(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive|-f\s+-r|-r\s+-f|-r\b.*-f|-f\b.*-r)\b', "Destructive file removal (`rm -rf`)"),
    (r'\bgit\s+push\s+.*(-f|--force)\b', "Force pushing git branch (`git push --force`)"),
    (r'\bDROP\s+TABLE\b', "Database drop table query (`DROP TABLE`)"),
    (r'\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z0-9_.]+', "Database table truncation query (`TRUNCATE TABLE`)"),
]

def is_unqualified_delete(cmd: str) -> bool:
    """Detects DELETE FROM statements that lack a WHERE clause."""
    upper_cmd = cmd.upper()
    if "DELETE" in upper_cmd and "FROM" in upper_cmd:
        match = re.search(r'\bDELETE\s+FROM\s+([a-zA-Z0-9_.`"]+)', cmd, re.IGNORECASE)
        if match:
            rest_of_query = cmd[match.end():].upper()
            if "WHERE" not in rest_of_query:
                return True
    return False

def log_blocked(command: str, project_path: str, reason: str, log_file: str = None):
    if not log_file:
        home_dir = os.path.expanduser("~")
        log_dir = os.path.join(home_dir, ".claude", "hooks")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] REASON: {reason} | PATH: {project_path} | COMMAND: {command}\n"
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not write to log file {log_file}: {e}\n")

def evaluate_command(command: str, project_path: str = None, log_file: str = None):
    if not project_path:
        project_path = os.getcwd()

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, project_path, reason, log_file)
            return False, f"BLOCKED: {reason} is prohibited for safety."

    if is_unqualified_delete(command):
        reason = "Unqualified SQL DELETE query without a WHERE clause (`DELETE FROM table`)"
        log_blocked(command, project_path, reason, log_file)
        return False, f"BLOCKED: {reason} is prohibited for safety."

    return True, "ALLOWED"

def main():
    command = ""
    project_path = os.getcwd()

    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read().strip()
            if raw_input:
                try:
                    payload = json.loads(raw_input)
                    if isinstance(payload, dict):
                        command = payload.get("tool_input", {}).get("command", "") or payload.get("command", "")
                        project_path = payload.get("cwd", os.getcwd())
                except json.JSONDecodeError:
                    command = raw_input
        except Exception:
            pass

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    if not command:
        sys.exit(0)

    is_allowed, msg = evaluate_command(command, project_path)

    if not is_allowed:
        sys.stderr.write(f"\n🛑 [Claude Code Hook Blocked Command]\n{msg}\nAttempted: {command}\n\n")
        output = {
            "decision": "block",
            "reason": msg,
            "command": command
        }
        print(json.dumps(output))
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
