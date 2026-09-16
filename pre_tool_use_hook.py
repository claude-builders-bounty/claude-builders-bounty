"""Claude Code Pre-Tool-Use Hook that blocks destructive bash commands."""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Incomplete initial implementation for baseline
DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"DROP\s+TABLE",
    r"git\s+push\b.*?(?:--force|-f|\+)",
    r"TRUNCATE",
    r"DELETE\s+FROM\s+(?!.*\bWHERE\b)",
]

def is_command_dangerous(command: str) -> tuple[bool, str]:
    cmd_clean = command.strip()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_clean, re.IGNORECASE):
            return True, f"Blocked: matched forbidden pattern '{pattern}'"
    return False, ""

def log_blocked(command: str, project_path: str = ".", log_file: Path = Path("blocked.log")):
    timestamp = datetime.now(timezone.utc).isoformat()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] PROJECT: {project_path} | BLOCKED: {command}\n")

def inspect_command(command: str, project_path: str = ".") -> bool:
    dangerous, reason = is_command_dangerous(command)
    if dangerous:
        log_blocked(command, project_path)
        print(f"[SECURITY ALERT] Destructive command prevented: {command}\nReason: {reason}", file=sys.stderr)
        return False
    return True