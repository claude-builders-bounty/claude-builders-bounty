# Claude Code Pre-Tool-Use Security Hook

Intercepts and blocks destructive bash and SQL commands before execution by Claude Code.

## Blocked Command Patterns
- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE` / `TRUNCATE TABLE`
- `DELETE FROM ...` without a `WHERE` clause

Every blocked command is audited and logged to `~/.claude/hooks/blocked.log` with timestamp, directory context, and the full command payload.

## Installation in 2 Commands
```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
bash claude-builders-bounty/hooks/install.sh
```

## Running Tests
```bash
python3 hooks/test_pre_tool_use.py
```
