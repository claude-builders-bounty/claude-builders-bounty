# Claude Code Safety Hook 🛡️

A `pre-tool-use` hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks destructive bash commands before they can cause damage.

## Blocked Patterns
- `rm -rf` (Recursive forced removal)
- `DROP TABLE` (SQL database destruction)
- `git push --force` (Repository history overwrite)
- `TRUNCATE` (SQL table clearing)
- `DELETE FROM` (SQL deletions without a `WHERE` clause)

## Installation

Install in 2 commands:

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## Logging
Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with the following format:
`[TIMESTAMP] | BLOCKED: [COMMAND] | PATTERN: [PATTERN] | PATH: [PROJECT_PATH]`

---
*Created by Michael Sovereign V7.0.0*
