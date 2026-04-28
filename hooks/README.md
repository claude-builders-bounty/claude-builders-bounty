# Pre-Tool-Use Safety Hook

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they execute.

## Blocked Patterns

| Pattern | Example |
|---|---|
| `rm -rf` | `rm -rf /`, `rm -rf *`, `rm -r -f node_modules` |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;`, `DROP DATABASE prod;` |
| `TRUNCATE` | `TRUNCATE TABLE orders;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |
| `git push --force` | `git push --force origin main`, `git push -f` |

## Installation

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

Or, in two commands:

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## How It Works

1. Claude Code calls the hook before executing any Bash tool
2. The hook inspects the command against a set of dangerous regex patterns
3. If matched, the command is **blocked**, logged to `~/.claude/hooks/blocked.log`, and Claude sees a clear reason message
4. Safe commands pass through with zero latency

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with:

- **Timestamp** (UTC)
- **Reason** (which pattern matched)
- **Command** (first 500 chars)
- **Project path** (working directory)

## Temporarily Disabling

```bash
mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.bak
# ... do your thing ...
mv ~/.claude/hooks/pre-tool-use.bak ~/.claude/hooks/pre-tool-use
```

## Requirements

- Python 3.6+
- Claude Code with hooks enabled
