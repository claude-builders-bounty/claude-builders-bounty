# Destructive Bash Blocker Hook

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install in 2 Commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-bash.py ~/.claude/hooks/block-destructive-bash.py
python3 - <<'PY'
from pathlib import Path
import json
settings = Path.home() / ".claude" / "settings.json"
settings.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(settings.read_text()) if settings.exists() else {}
data.setdefault("hooks", {})["PreToolUse"] = [{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/block-destructive-bash.py"}]}]
settings.write_text(json.dumps(data, indent=2) + "
")
PY
```

## What It Blocks

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause before the statement terminator

Normal Bash commands return with no output, so Claude Code continues without interruption.

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line includes the UTC timestamp, project path, block reason, and attempted command.

## Example Hook Settings

A ready-to-copy Claude Code settings snippet is included at `hooks/settings.example.json`.
