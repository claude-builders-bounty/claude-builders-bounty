# Destructive Command Blocker for Claude Code

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous
bash commands before they can be executed. Protects against accidental
filesystem destruction, git force-pushes, and dangerous database operations.

## Installation

```bash
mkdir -p ~/.claude/hooks && curl -sL https://raw.githubusercontent.com/z1234hz/claude-builders-bounty/main/hooks/destructive-command-blocker/pre-tool-use -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Category | Patterns |
|----------|----------|
| **Filesystem** | `rm -rf /`, `rm -rf --no-preserve-root`, `mkfs.*`, `dd if=/dev/zero of=/dev/sda`, `shutdown -h now` |
| **Git** | `git push --force`, `git reset --hard HEAD~`, `git branch -D` (on main branches) |
| **Database** | `DROP TABLE`, `TRUNCATE TABLE`, `DELETE FROM` without `WHERE`, `DROP DATABASE`, `ALTER TABLE ... DROP` |

## How It Works

1. Claude Code calls the `pre-tool-use` hook before executing a tool
2. The hook reads the tool call as JSON from stdin
3. If the tool is a bash command, it checks the command against dangerous patterns
4. Safe commands pass through without any delay or message
5. Dangerous commands are blocked with a clear explanation

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- The attempted command
- The pattern that was matched

## Temporary Bypass

If you need to run a command that is incorrectly flagged:

```bash
mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.disabled
# Run your command
mv ~/.claude/hooks/pre-tool-use.disabled ~/.claude/hooks/pre-tool-use
```

## Requirements

- Python 3 (for JSON parsing from stdin)
- Claude Code (to use the hook)

## License

MIT
