# Pre-Tool-Use Destructive Command Blocker Hook

A security hook for Claude Code that intercepts and blocks dangerous commands before execution.

## Blocked Command Patterns
- `rm -rf` (recursive force directory deletion)
- `DROP TABLE` (SQL table deletion)
- `git push --force` / `git push -f`
- `TRUNCATE` (SQL table truncation)
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are automatically recorded to `~/.claude/hooks/blocked.log` with timestamp, project directory, and command details.

## Quick Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_block_destructive.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py
```
