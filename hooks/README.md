# Claude Code PreToolUse Safety Hook

Blocks destructive Bash commands before Claude Code executes them.

This hook reads Claude Code `PreToolUse` JSON from stdin, inspects Bash commands,
logs blocked attempts, and returns a Claude Code permission denial when a command
matches a destructive pattern.

## Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

## Install in 2 commands

Run from this repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_safety.py ~/.claude/hooks/pre_tool_use_safety.py && chmod +x ~/.claude/hooks/pre_tool_use_safety.py
python3 - <<'PY'
import json
from pathlib import Path
settings = Path.home() / ".claude" / "settings.json"
settings.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(settings.read_text()) if settings.exists() and settings.read_text().strip() else {}
hooks = data.setdefault("hooks", {})
entries = hooks.setdefault("PreToolUse", [])
entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use_safety.py"}]}
if entry not in entries:
    entries.append(entry)
settings.write_text(json.dumps(data, indent=2) + "\n")
PY
```

## Log file

This hook appends JSON lines to `~/.claude/hooks/blocked.log`. Use your normal
log-retention tooling if the hook runs in a high-volume environment; for example,
rotate or truncate this file periodically.

Each entry includes:

- timestamp
- attempted command
- project path
- block reason

Example:

```json
{"attempted_command":"rm -rf build","project_path":"/tmp/project","reason":"recursive forced removal with rm -rf","timestamp":"2026-06-04T12:00:00+00:00"}
```

## Claude Code settings example

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_safety.py"
          }
        ]
      }
    ]
  }
}
```

## Manual test

Allowed command:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"npm test"},"cwd":"/tmp/project"}' \
  | python3 hooks/pre_tool_use_safety.py
```

Blocked command:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/project"}' \
  | python3 hooks/pre_tool_use_safety.py
```

The blocked command prints a JSON `permissionDecision: deny` response and writes
to `~/.claude/hooks/blocked.log`.
