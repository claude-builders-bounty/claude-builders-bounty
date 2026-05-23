# Pre-tool-use hook: block destructive bash commands

This hook blocks dangerous bash commands before execution and logs every blocked attempt.

## Install (2 commands)
```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use-block.py ~/.claude/hooks/
python - <<'PY'
import json, pathlib
p=pathlib.Path.home()/'.claude'/'settings.json'
p.parent.mkdir(parents=True, exist_ok=True)
cfg={}
if p.exists():
    cfg=json.loads(p.read_text() or '{}')
cfg.setdefault('hooks',{})['PreToolUse']=[{"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/pre-tool-use-block.py"}]}]
p.write_text(json.dumps(cfg,indent=2))
print('updated',p)
PY
```

## What it blocks
- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

## Log format
Blocked events are appended to:
`~/.claude/hooks/blocked.log`

Each line contains:
- timestamp (UTC ISO-8601)
- project path
- attempted command

## Behavior
- Returns exit code `2` for blocked commands (prevents tool execution)
- Prints a clear blocking reason to stderr
- Returns `0` for normal commands (no interference)
