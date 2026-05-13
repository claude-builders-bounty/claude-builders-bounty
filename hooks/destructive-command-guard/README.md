# Destructive Command Guard

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-command-guard/destructive-command-guard.py ~/.claude/hooks/destructive-command-guard.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home()/'.claude'/'settings.json'
p.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(p.read_text()) if p.exists() else {}
settings['hooks'] = {'PreToolUse': [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'python3 ~/.claude/hooks/destructive-command-guard.py'}]}]}
p.write_text(json.dumps(settings, indent=2) + '\n')
PY
```

## What it blocks

- `rm -rf` / `rm -fr` style recursive force deletion
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- timestamp
- attempted command
- project path
- block reason

Normal Bash commands produce no hook decision and proceed normally.
