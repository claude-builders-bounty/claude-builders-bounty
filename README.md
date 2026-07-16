# Pre-Tool-Use Hook: Block Destructive Commands

Claude Code hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
# Option 1: Bash version
mkdir -p ~/.claude/hooks && cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh

# Option 2: Python version
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
```

## Blocked Commands

- `rm -rf` — Recursive force delete
- `DROP TABLE` — SQL table destruction
- `TRUNCATE` — Table truncation
- `git push --force` / `git push -f` — Forced overwrite
- `DELETE FROM` without WHERE — Mass data deletion

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (UTC)
- Attempted command
- Current project path

## How It Works

The hook runs as a pre-tool-use interceptor in Claude Code. When a command matches a dangerous pattern, it:

1. Logs the attempt to `blocked.log`
2. Displays a clear safety message explaining why it was blocked
3. Suggests safer alternatives
4. Prevents the command from executing

## Bounty

Addresses the [$100 HOOK] Pre-tool-use hook that blocks destructive bash commands (Issue #3)
