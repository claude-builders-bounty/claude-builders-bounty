#!/usr/bin/env python3
"""pre-tool-use hook — blocks destructive bash commands before execution.

Claude Code hooks format: reads JSON from stdin, returns JSON to stdout.
"""

import sys, json, os, re
from datetime import datetime, timezone

LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

DANGEROUS = [
    (r"rm\s+-rf", "rm -rf"),
    (r"rm\s+-r\s", "rm -r (recursive remove)"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE", re.IGNORECASE),
    (r"\bTRUNCATE\b", "TRUNCATE", re.IGNORECASE),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM without WHERE", re.IGNORECASE),
    (r"git\s+push\s+.*--force", "git push --force"),
    (r"git\s+push\s+.*-f\b", "git push -f"),
    (r"sudo\s+rm\s+-rf", "sudo rm -rf"),
    (r">\s*/dev/sd[a-z]", "overwrite block device"),
    (r"mkfs\.", "mkfs (format filesystem)"),
    (r"dd\s+if=.*of=/dev/sd", "dd to block device"),
    (r":\(\)\s*\{", "fork bomb"),
    (r"chmod\s+-R\s+777\s+/", "chmod -R 777 /"),
    (r"chown\s+-R\s+.*\s+/", "chown -R /"),
]


def log_block(command, project_path, reason):
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project": project_path,
        "reason": reason,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow"}))
        return

    command = data.get("tool_input", {}).get("command", "")
    project = os.getcwd()

    if not command:
        print(json.dumps({"decision": "allow"}))
        return

    # Normalize: collapse whitespace
    normalized = " ".join(command.split())

    for pattern, label, *flags in DANGEROUS:
        flag = flags[0] if flags else 0
        if re.search(pattern, normalized, flag):
            reason = f"Blocked dangerous pattern: {label}"
            log_block(normalized, project, label)

            result = {
                "decision": "block",
                "reason": (
                    f"🚫 BLOCKED: This command matches a dangerous pattern ({label}).\n"
                    f"   Command: {normalized[:120]}\n"
                    f"   If you are certain this is safe, review and run it manually."
                ),
            }
            print(json.dumps(result))
            return

    # Allow everything else
    print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
