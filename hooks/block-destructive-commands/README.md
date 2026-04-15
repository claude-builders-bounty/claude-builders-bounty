# Claude Code Pre-tool-use Hook: Block Destructive Commands

A safety hook that intercepts and blocks dangerous bash commands before execution in Claude Code.

## Installation (2 commands)

```bash
# 1. Clone/download the hook
mkdir -p ~/.claude/hooks && curl -sL https://raw.githubusercontent.com/YOUR_FORK/claude-safety-hooks/main/pre-tool-use.sh -o ~/.claude/hooks/pre-tool-use.sh

# 2. Make it executable
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

That's it! The hook will automatically block dangerous commands in Claude Code.

## What It Blocks

- `rm -rf` - Recursive force delete
- `DROP TABLE` - SQL table deletion
- `TRUNCATE` - SQL table clearing  
- `DELETE FROM` without WHERE - Unchecked SQL deletions
- `git push --force` - Force push to git

## Blocked Commands Log

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path

View the log:
```bash
cat ~/.claude/hooks/blocked.log
```

## How It Works

The hook intercepts bash tool calls before execution and checks for dangerous patterns. If found, it returns an error message explaining why the command was blocked.

## Testing

Try asking Claude to run a dangerous command - it should be blocked with an explanation.

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use.sh
```

## License

MIT
