import json
import os
from typing import Any


def load_event(raw_input: str) -> dict[str, Any]:
    """Parse the Claude Code hook JSON payload."""
    if not raw_input.strip():
        return {}

    try:
        event = json.loads(raw_input)
    except json.JSONDecodeError:
        return {}

    return event if isinstance(event, dict) else {}


def extract_command(event: dict[str, Any]) -> str:
    """Read the Bash command from common Claude Code hook payload shapes."""
    containers = [
        event.get("tool_input"),
        event.get("input"),
        event.get("parameters"),
        event,
    ]

    for container in containers:
        if not isinstance(container, dict):
            continue
        for key in ("command", "cmd"):
            value = container.get(key)
            if isinstance(value, str):
                return value

    return ""


def project_path(event: dict[str, Any]) -> str:
    """Resolve the project path Claude Code is operating in."""
    for key in ("cwd", "project_dir", "workspace", "workspace_dir"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value

    env_project = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project:
        return env_project

    return os.getcwd()

