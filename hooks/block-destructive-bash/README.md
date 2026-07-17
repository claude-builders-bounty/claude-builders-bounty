# Block destructive bash (Claude Code pre-tool-use hook)

Stops `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without `WHERE` before they run. Safe commands pass through.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

```bash
# Add to ~/.claude/settings.json (merge into existing hooks if you already have some):
# {
#   "hooks": {
#     "PreToolUse": [{
#       "matcher": "Bash",
#       "hooks": [{
#         "type": "command",
#         "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
#       }]
#     }]
#   }
# }
python3 -c "import json,pathlib;p=pathlib.Path.home()/'.claude'/'settings.json';p.parent.mkdir(parents=True,exist_ok=True);d=json.loads(p.read_text()) if p.exists() else {};d.setdefault('hooks',{}).setdefault('PreToolUse',[]).append({'matcher':'Bash','hooks':[{'type':'command','command':'python3 ~/.claude/hooks/block_destructive_bash.py'}]});p.write_text(json.dumps(d,indent=2))"
```

If you prefer not to auto-edit settings, only run the first command and paste the JSON snippet by hand.

## What gets blocked

| Pattern | Example |
|---------|---------|
| `rm -rf` / `rm -fr` | `rm -rf /tmp/proj` |
| `DROP TABLE` | `sqlite3 app.db 'DROP TABLE users'` |
| `git push --force` / `-f` | `git push --force origin main` |
| `TRUNCATE` | `TRUNCATE TABLE sessions` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users` |

Normal work is allowed: `ls`, `git status`, `rm file.txt` (no `-rf`), `DELETE FROM t WHERE id=1`.

## Logging

Every block appends one line to `~/.claude/hooks/blocked.log`:

```text
2026-07-17T12:00:00Z	project=/path/to/repo	reason=rm -rf ...	command=rm -rf node_modules
```

## Manual test

```bash
python3 block_destructive_bash.py --command "rm -rf /" --cwd /tmp --log /tmp/blocked-test.log; echo exit:$?
# expect exit 2 and a log line

python3 block_destructive_bash.py --command "ls -la" --cwd /tmp; echo exit:$?
# expect exit 0
```
