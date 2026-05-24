# Block destructive Bash commands hook

Claude Code `PreToolUse` hook that stops high-risk Bash commands before execution and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks ~/.claude/hooks/block-destructive-bash && cp hooks/block-destructive-bash/block_destructive_bash.py ~/.claude/hooks/block-destructive-bash/
python3 - <<'PY'
import json, pathlib
p=pathlib.Path('~/.claude/settings.json').expanduser(); data=json.loads(p.read_text() if p.exists() else '{}'); data.setdefault('hooks',{}).setdefault('PreToolUse',[]).append({'matcher':'Bash','hooks':[{'type':'command','command':'python3 ~/.claude/hooks/block-destructive-bash/block_destructive_bash.py'}]}); p.write_text(json.dumps(data, indent=2)+'\n')
PY
```

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause

Normal Bash commands exit successfully and are not logged.
