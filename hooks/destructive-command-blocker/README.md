# Destructive command blocker for Claude Code

A Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they execute.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-command-blocker/pre-tool-use ~/.claude/hooks/pre-tool-use-destructive-blocker && chmod +x ~/.claude/hooks/pre-tool-use-destructive-blocker
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
data = json.loads(p.read_text()) if p.exists() else {}
data.setdefault("hooks", {}).setdefault("PreToolUse", []).append({"matcher":"Bash","hooks":[{"type":"command","command":str(pathlib.Path.home()/".claude/hooks/pre-tool-use-destructive-blocker")}]})
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2) + "\n")
PY
```

## What it blocks

- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM ...` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a UTC timestamp, attempted command, project path, and block reason. Safe Bash commands exit normally and do not interfere.

## Test

```bash
python3 tests/test_destructive_command_blocker.py
```
