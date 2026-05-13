# Claude Code destructive command hook

This bounty submission adds a Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_commands.py ~/.claude/hooks/
python3 - <<'PY'
import json, pathlib
settings = pathlib.Path.home() / ".claude" / "settings.json"
settings.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(settings.read_text()) if settings.exists() else {}
data.setdefault("hooks", {})["PreToolUse"] = [{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/block_destructive_commands.py"}]}]
settings.write_text(json.dumps(data, indent=2) + "\n")
PY
```

Alternatively, copy `hooks/settings.example.json` into `~/.claude/settings.json` if you do not already have Claude Code settings.

## What it blocks

- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM ...` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, project path, and reason.

## Test

```bash
python3 -m unittest discover -s tests
```
