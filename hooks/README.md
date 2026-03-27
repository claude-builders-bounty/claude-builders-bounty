# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they execute.

## Blocked Patterns

| Pattern | Risk |
|---------|------|
| `rm -rf` | Recursive force delete — permanently destroys files |
| `DROP TABLE` | Removes an entire database table |
| `TRUNCATE` | Removes all rows from a table without logging |
| `git push --force` / `-f` | Overwrites remote git history |
| `DELETE FROM` (no `WHERE`) | Deletes every row in a table |

## Installation

```bash
cp hooks/pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

That's it. The hook activates on the next Claude Code session.

## How It Works

1. Claude Code calls the hook with a JSON payload before executing any tool
2. The hook checks if the tool is `Bash` and inspects the command
3. If a destructive pattern is matched, the hook:
   - Logs the attempt to `~/.claude/hooks/blocked.log` (timestamp, command, project path)
   - Returns a clear explanation to Claude about why the command was blocked
   - Exits with code `2` to prevent execution
4. Safe commands pass through with exit code `0`

## Logging

Every blocked command is appended to `~/.claude/hooks/blocked.log`:

```
[2026-03-28T10:15:30Z] BLOCKED: rm -rf | command: rm -rf /var/data | project: /home/user/myproject
```

## Testing

Run the test suite (20 test cases):

```bash
bash hooks/test_hook.sh
```

## Requirements

- Bash 4+
- Python 3 (used only for JSON parsing — no external dependencies)
