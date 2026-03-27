# Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

A small Claude Code pre-tool-use hook that blocks dangerous bash commands before execution.

## Blocks
- `rm -rf`
- `git push --force`, `git push -f`, `git push --force-with-lease`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

When a command is blocked, the hook logs it to `~/.claude/hooks/blocked.log` with:
- timestamp
- attempted command
- project path

## Install
```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

## Expected hook behavior
Place this file in Claude Code's pre-tool-use hooks location:
- `~/.claude/hooks/pre-tool-use.py`

The hook reads a JSON event from stdin and returns JSON:
- allow: `{"action":"allow"}`
- deny: `{"action":"deny","message":"..."}`

## Quick test
Blocked:
```bash
printf '%s' '{"tool_name":"bash","tool_input":{"command":"rm -rf /tmp/test","cwd":"/tmp/demo"}}' | python3 pre-tool-use.py
```

Allowed:
```bash
printf '%s' '{"tool_name":"bash","tool_input":{"command":"ls -la","cwd":"/tmp/demo"}}' | python3 pre-tool-use.py
```
