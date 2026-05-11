# Destructive Bash Command Hook

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before execution.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-bash.py ~/.claude/hooks/block-destructive-bash.py
python3 - <<'PY'
import json, pathlib
settings = pathlib.Path.home() / ".claude" / "settings.json"
data = json.loads(settings.read_text()) if settings.exists() else {}
data.setdefault("hooks", {})["PreToolUse"] = [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block-destructive-bash.py"}]}]
settings.write_text(json.dumps(data, indent=2) + "\n")
PY
```

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with timestamp, matched rule, project path, and attempted command.

Normal Bash commands exit `0` and continue without output. Blocked commands exit `2` and write a clear explanation to stderr so Claude Code can recover.
