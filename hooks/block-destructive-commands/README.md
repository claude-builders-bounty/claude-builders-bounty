# Block Destructive Commands Hook

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## Setup (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp block-destructive.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Irreversible file deletion |
| `git push --force` | Rewrites shared history |
| `DROP TABLE` | Permanently destroys database tables |
| `TRUNCATE` | Deletes all rows without WHERE |
| `DELETE FROM` (no WHERE) | Deletes all rows in table |

## How it works

The hook reads the tool input JSON from stdin, extracts the command, and checks it against dangerous patterns. If a match is found, it:

1. Logs the attempt to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
2. Returns exit code 1 with a clear explanation message
3. Claude Code receives the message and avoids executing the command

## Log format

```
2026-04-28T12:00:00Z | command: rm -rf /tmp/test | project: /home/user/myproject
```

## Requirements

- Python 3 (for JSON parsing)
- Bash
