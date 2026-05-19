# Claude Code Pre-Tool-Use Safety Hook

Blocks destructive bash commands before they execute.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
ln -s "$(pwd)/pre-tool-use-blocker.py" ~/.claude/hooks/pre-tool-use
```

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete |
| `git push --force` | Force overwrite remote history |
| `DROP TABLE` | Database table deletion |
| `TRUNCATE TABLE` | Table data wipe |
| `DELETE FROM` without WHERE | Unconditional row deletion |
| `DELETE FROM ... WHERE 1=1` | Tautology = unconditional deletion |
| `mkfs.*` | Filesystem format |
| `dd if=* of=/dev/*` | Raw disk overwrite |
| `> /dev/sd*` | Redirect to block device |
| Fork bombs | Resource exhaustion |

## Log Format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-19T21:30:00] BLOCKED: rm -rf: recursive force delete
  Command: rm -rf /
  Project: /home/user/myproject
  ============================================================
```

## How It Works

Claude Code calls this hook before executing any tool. The hook:

1. Checks if the tool is `bash`
2. Runs the command against a regex pattern list
3. If matched: logs the attempt, blocks execution, and shows a clear message
4. If safe: allows execution to proceed normally

## Testing

```bash
echo '{"tool": "bash", "command": "rm -rf /tmp/test"}' | python3 pre-tool-use-blocker.py
# Should output: {"allowed": false, "message": "..."}

echo '{"tool": "bash", "command": "ls -la"}' | python3 pre-tool-use-blocker.py
# Should output: {"allowed": true}
```
