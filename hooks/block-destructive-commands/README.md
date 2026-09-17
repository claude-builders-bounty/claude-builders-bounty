# Destructive Command Blocker Hook for Claude Code

> Pre-tool-use security hook (in Bash and Python) preventing accidental execution of destructive shell and database commands during Claude Code sessions.

## Protected Patterns

- `rm -rf` / `rm -fr` (recursive force directory deletions)
- `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` / `DROP VIEW`
- `git push --force` / `git push -f` / force lease overrides
- `TRUNCATE` / `TRUNCATE TABLE`
- `DELETE FROM` without a `WHERE` clause (safe bounded queries remain allowed)

## Audit Logging

Every intercepted violation is automatically logged with UTC timestamp, trigger rule, and full command to:
`~/.claude/hooks/blocked.log`

## Installation

```bash
mkdir -p ~/.claude/hooks

# Choose either the zero-dependency Bash implementation:
cp hooks/block-destructive-commands/pre-tool-use.sh ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use

# Or the Python 3 implementation:
# cp hooks/block-destructive-commands/pre_tool_use.py ~/.claude/hooks/pre-tool-use
# chmod +x ~/.claude/hooks/pre-tool-use
```

## Verification

Run the included test harness:
```bash
./hooks/block-destructive-commands/test_hooks.sh
```
Validates 20 distinct safe and dangerous command edge cases across both runtimes.
