# Destructive Bash Command Blocker for Claude Code

A Claude Code `PreToolUse` hook that blocks dangerous Bash commands before execution and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Install in 2 commands

```bash
mkdir -p .claude/hooks && cp destructive-command-hook/.claude/hooks/block-destructive-bash.py .claude/hooks/
python3 - <<'PY'
import json, pathlib
p=pathlib.Path('.claude/settings.json')
data=json.loads(p.read_text()) if p.exists() else {}
data.setdefault('hooks', {}).setdefault('PreToolUse', []).append({'matcher':'Bash','hooks':[{'type':'command','command':'"$CLAUDE_PROJECT_DIR"/.claude/hooks/block-destructive-bash.py'}]})
p.write_text(json.dumps(data, indent=2) + '\n')
PY
```

## Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

## Log format

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as tab-separated lines:

```text
timestamp<TAB>project_path<TAB>pattern_name<TAB>attempted_command
```

## Manual settings example

See `settings.example.json` for a project-level `.claude/settings.json` configuration.
