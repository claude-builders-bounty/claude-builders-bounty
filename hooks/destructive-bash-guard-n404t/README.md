# Destructive Bash Guard for Claude Code

PreToolUse hook that blocks destructive Bash commands before Claude Code can run them.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp destructive_bash_guard.py ~/.claude/hooks/destructive_bash_guard.py && chmod +x ~/.claude/hooks/destructive_bash_guard.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / '.claude' / 'settings.json'
p.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(p.read_text()) if p.exists() else {}
data.setdefault('hooks', {}).setdefault('PreToolUse', []).append({'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': str(pathlib.Path.home() / '.claude' / 'hooks' / 'destructive_bash_guard.py')}]})
p.write_text(json.dumps(data, indent=2) + '\n')
PY
```

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

## Logging

Every blocked attempt appends one line to:

```text
~/.claude/hooks/blocked.log
```

Fields: UTC timestamp, project path, rule name, attempted command.

## Claude Code behavior

The hook exits with code `2` for blocked commands and prints a clear message to stderr:

```text
Blocked destructive Bash command: rm -rf. Attempt logged to ~/.claude/hooks/blocked.log. Rewrite command to avoid destructive action.
```

Normal Bash commands exit `0` and are not logged.
