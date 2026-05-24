# Block Destructive Commands Hook

Claude Code `PreToolUse` hook that blocks dangerous bash commands before execution.

## Install (2 commands)

```bash
cp -r hooks/block-destructive ~/.claude/hooks/block-destructive
# Merge hooks/block-destructive/hooks.example.json into ~/.claude/settings.json
```

Or copy `block_destructive.py` to `~/.claude/hooks/block_destructive.py` and register it in your Claude Code hooks config.

## Blocked patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Irreversible file deletion |
| `DROP TABLE` | Database table destruction |
| `git push --force` / `git push -f` | Remote history overwrite |
| `TRUNCATE` | Table wipe |
| `DELETE FROM` without `WHERE` | Full-table delete |

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
2026-05-24T19:45:00+00:00	project=/path/to/repo	command='rm -rf /'	reason=`rm -rf` deletes files irreversibly
```

## Hook behavior

- Exit `0` — allow the command
- Exit `2` — block and show a clear stderr message to Claude
- Normal safe commands are not affected

## Test locally

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/tmp/project"}' | python hooks/block-destructive/block_destructive.py
# exit code 2, message on stderr
```

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp/project"}' | python hooks/block-destructive/block_destructive.py
# exit code 0
```

## References

- [Claude Code hooks documentation](https://docs.anthropic.com/claude-code/hooks)
