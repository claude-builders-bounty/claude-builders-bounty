# Claude Code `PreToolUse` Destructive Command Blocker Hook (Bounty Issue #3)

Intercepts and blocks destructive Bash and SQL commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause) before Claude Code can execute them, and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 -c 'import json,pathlib;p=pathlib.Path.home()/".claude"/"settings.json";d=json.loads(p.read_text()) if p.exists() else {};d.setdefault("hooks",{})["PreToolUse"]=[{"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/block_destructive_bash.py"}]}];p.write_text(json.dumps(d,indent=2))'
```

## Blocked Patterns & Log Format (`~/.claude/hooks/blocked.log`)

- `rm -rf` / `rm -fr` / `rm --recursive --force`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM <table>` without a `WHERE` clause

Sample `~/.claude/hooks/blocked.log` entry:
```text
2026-11-20T11:50:00Z | project=/workspace/my-app | reason=Blocked destructive command: 'rm -rf' recursive force deletion is prohibited. | command=rm -rf ./dist
```
