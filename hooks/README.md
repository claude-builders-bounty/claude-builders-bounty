# Destructive Bash & SQL Command Blocker Hook ($100 Bounty Solution)

A Claude Code `pre-tool-use` hook (`pre_tool_use.py`) that intercepts and blocks dangerous commands before execution:
- `rm -rf`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked command is appended to `~/.claude/hooks/blocked.log` with ISO-8601 timestamp, project path, and attempted command.

## Installation (2 Commands)
```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
```
