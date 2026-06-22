# Pre-Tool-Use Hook: Block Destructive Commands

Closes [claude-builders-bounty#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) — **$100 Opire bounty**.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_commands.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_commands.py
```

Merge `settings.snippet.json` into `~/.claude/settings.json` (or your project's `.claude/settings.json`).

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` | Irreversible file deletion |
| `git push --force` / `-f` | Rewrites remote history |
| `DROP TABLE` | Destroys DB tables |
| `TRUNCATE` | Wipes table data |
| `DELETE FROM` without `WHERE` | Deletes all rows |

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
2026-06-22T10:00:00+00:00	project=/path/to/repo	command='rm -rf /'	reason=...
```

## Test

```bash
python -m pytest tests/ -q
```

Manual smoke test:

```bash
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"}}' | python block_destructive_commands.py
```

Expected stdout:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", ...}}
```

Safe commands produce no output and exit 0.
