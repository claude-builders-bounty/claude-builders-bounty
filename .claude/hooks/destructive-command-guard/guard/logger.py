import json
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_attempt(
    command: str,
    project_path: str,
    rule_id: str,
    reason: str,
    log_path: Path = DEFAULT_LOG_PATH,
) -> None:
    """Append a blocked command event as JSON Lines."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "project_path": project_path,
        "command": command,
        "rule_id": rule_id,
        "reason": reason,
    }

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")

