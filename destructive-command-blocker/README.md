# Destructive Command Blocker

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Installation

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-blocker/block_destructive_commands.py ~/.claude/hooks/block_destructive_commands.py
python3 - <<'PY'
import json
from pathlib import Path
settings = Path.home() / ".claude" / "settings.json"
settings.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(settings.read_text()) if settings.exists() else {}
data.setdefault("hooks", {}).setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_destructive_commands.py"}],
}
if entry not in data["hooks"]["PreToolUse"]:
    data["hooks"]["PreToolUse"].append(entry)
settings.write_text(json.dumps(data, indent=2) + "\n")
PY
```

## What It Blocks

- `rm` commands that combine recursive and force flags, such as `rm -rf`.
- `DROP TABLE`.
- `git push --force`.
- `TRUNCATE`.
- `DELETE FROM` statements without a `WHERE` clause.

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a UTC timestamp, attempted command, project path, and reason.

Normal Bash commands are allowed without output.

## Configuration Example

See `settings.example.json` for the Claude Code hooks format:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_commands.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python3 -m unittest destructive-command-blocker/test_block_destructive_commands.py
```
