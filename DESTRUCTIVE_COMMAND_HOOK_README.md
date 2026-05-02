# Claude Code destructive command guard

A `pre-tool-use` hook for Claude Code that blocks risky Bash commands before they run.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM ...` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
python3 -c "import json,pathlib; p=pathlib.Path.home()/'.claude/settings.json'; p.parent.mkdir(parents=True,exist_ok=True); data=json.loads(p.read_text()) if p.exists() else {}; data.setdefault('hooks',{}).setdefault('PreToolUse',[]).append({'matcher':'Bash','hooks':[{'type':'command','command':str(pathlib.Path.home()/'.claude/hooks/block_destructive_bash.py')}]}); p.write_text(json.dumps(data,indent=2)+'\n')"
```

## Local test

Blocked command:

```bash
printf '%s
' '{"tool_name":"Bash","tool_input":{"command":"rm -rf build","cwd":"/tmp/project"}}' | hooks/block_destructive_bash.py
```

Allowed command:

```bash
printf '%s
' '{"tool_name":"Bash","tool_input":{"command":"python3 -m pytest","cwd":"/tmp/project"}}' | hooks/block_destructive_bash.py
```

## Notes

The hook is intentionally conservative: it only exits non-zero for configured destructive patterns and returns success for normal Bash commands, non-Bash tools, or malformed/empty input. SQL matching is case-insensitive and treats `DELETE FROM users;` as destructive unless a `WHERE` clause appears before the statement terminator.
