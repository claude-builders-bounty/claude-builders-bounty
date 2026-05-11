# Block Destructive Bash Commands

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-bash/block_destructive_bash.py ~/.claude/hooks/
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
p.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(p.read_text() or "{}") if p.exists() else {}
data.setdefault("hooks", {}).setdefault("PreToolUse", []).append({"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 \"$HOME/.claude/hooks/block_destructive_bash.py\""}]})
p.write_text(json.dumps(data, indent=2) + "\n")
PY
```

The hook writes blocked attempts to `~/.claude/hooks/blocked.log`.

## Blocked Patterns

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Normal Bash commands exit silently and continue unchanged.
