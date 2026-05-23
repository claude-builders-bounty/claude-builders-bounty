# Claude Code Pre-Tool-Use Hook

A security hook for Claude Code that blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
# Install the hook
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Description |
|---------|-------------|
| `rm -rf /` | Root directory deletion |
| `rm -rf node_modules .git` | Recursive force delete |
| `DROP TABLE` | Database table deletion |
| `TRUNCATE TABLE` | Table truncation |
| `git push --force` / `-f` | Forced git push |
| `DELETE FROM table` (no WHERE) | Destructive SQL delete |

## How It Works

- Intercepts `Bash` tool calls before execution
- Checks command against dangerous patterns
- Blocks and logs blocked attempts to `~/.claude/hooks/blocked.log`
- Shows clear error message to Claude explaining why the command was blocked

## Log Format

```
[2026-05-22T18:00:00] BLOCKED: rm -rf /
  Reason: Root directory deletion
  Project: /path/to/project
```

## Uninstallation

```bash
rm ~/.claude/hooks/pre-tool-use
```

## Requirements

- Python 3.6+
- Claude Code