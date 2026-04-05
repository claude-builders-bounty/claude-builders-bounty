# Claude Code Destructive Command Block Hook

A [Claude Code](https://claude.ai/code) pre-tool-use hook that blocks destructive bash commands before they can execute.

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf <path>` | Recursive force delete — destroys data permanently |
| `git push --force` / `git push -f` | Force push — overwrites remote history |
| `DROP TABLE <name>` | SQL DROP TABLE — removes entire table |
| `DROP DATABASE <name>` | SQL DROP DATABASE — removes entire database |
| `TRUNCATE TABLE <name>` | SQL TRUNCATE — removes all rows from table |
| `DELETE FROM <table>` (no WHERE) | DELETE without WHERE — removes ALL rows |

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Installation

```bash
# 1. Copy the hook into your project (or ~/.claude/hooks/ for global)
cp -r hooks/ ~/.claude/hooks/

# 2. Register with Claude Code
claude code hooks add preToolUse ~/.claude/hooks/pre-tool-use.js
```

That's it — no configuration needed.

## How It Works

The hook intercepts all `Bash` tool calls before they execute. If a command matches a destructive pattern, it:

1. **Blocks the command** with a clear error message
2. **Logs the attempt** to `~/.claude/hooks/blocked.log` with timestamp, command, and project path

Non-destructive commands pass through normally with zero overhead.

## Uninstall

```bash
claude code hooks remove preToolUse
rm -rf ~/.claude/hooks/pre-tool-use.js
```

## Manual Override

If you need to run a blocked command, you can:

1. Run it directly in your terminal (bypassing Claude Code)
2. Ask the user to confirm, then temporarily remove the hook

## Log Format

```
[2026-04-05T12:00:00.000Z] BLOCKED | tool=Bash | project=/path/to/project | reason=<reason> | command=<command>
```
