import sys
import json
import os
import re
import datetime

def log_blocked_attempt(command, project_path):
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] Command: '{command}' | Project: '{project_path}'\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)

def main():
    # 1. Read JSON payload from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            # If stdin is empty, allow execution (fail-open)
            sys.exit(0)
        payload = json.loads(input_data)
    except Exception as e:
        # If parsing fails, default to allowing execution
        sys.exit(0)

    # 2. Extract tool name and command
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "")
    project_path = payload.get("session", {}).get("cwd", os.getcwd())

    # We only intercept Bash tool commands
    if tool_name.lower() != "bash" or not command:
        sys.exit(0)

    # 3. Check for blocked patterns
    blocked = False
    reason = ""

    # Pattern A: rm -rf
    if re.search(r'\brm\s+-[a-zA-Z]*([rf][a-zA-Z]*[rf]|[fr][a-zA-Z]*[fr])', command):
        blocked = True
        reason = "Execution blocked: 'rm -rf' command is destructive and not permitted."

    # Pattern B: DROP TABLE
    elif re.search(r'\bdrop\s+table\b', command, re.IGNORECASE):
        blocked = True
        reason = "Execution blocked: SQL 'DROP TABLE' is destructive and not permitted."

    # Pattern C: git push --force
    elif re.search(r'\bgit\s+push\b.*\b(--force|-f)\b', command, re.IGNORECASE):
        blocked = True
        reason = "Execution blocked: Force pushing ('git push --force' / '-f') is restricted."

    # Pattern D: TRUNCATE
    elif re.search(r'\btruncate\b', command, re.IGNORECASE):
        blocked = True
        reason = "Execution blocked: SQL 'TRUNCATE' is destructive and not permitted."

    # Pattern E: DELETE FROM without a WHERE clause
    elif re.search(r'\bdelete\s+from\b', command, re.IGNORECASE) and not re.search(r'\bwhere\b', command, re.IGNORECASE):
        blocked = True
        reason = "Execution blocked: SQL 'DELETE FROM' statement lacks a safety WHERE clause."

    # 4. If blocked, log, output to stderr, and exit with code 2
    if blocked:
        log_blocked_attempt(command, project_path)
        sys.stderr.write(reason + "\n")
        sys.exit(2)

    # Otherwise, allow execution
    sys.exit(0)

if __name__ == "__main__":
    main()
