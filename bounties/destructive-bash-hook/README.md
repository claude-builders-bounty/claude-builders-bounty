# Destructive Bash Command Blocker

A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before execution.

## Installation

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py hooks.json ~/.claude/hooks/
```

## Blocked Patterns

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /`, `rm -rf *` |
| `DROP TABLE/DATABASE` | `DROP TABLE users` |
| `TRUNCATE` | `TRUNCATE TABLE logs` |
| `DELETE FROM` without WHERE | `DELETE FROM users;` |
| `git push --force` | `git push -f origin main` |
| `git reset --hard` | `git reset --hard HEAD~5` |
| Dangerous dd | `dd if=/dev/zero of=/dev/sda` |
| Filesystem format | `mkfs.ext4 /dev/sda1` |
| Recursive chmod 777 on root | `chmod -R 777 /` |

## Logging

All blocked commands are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path
- Reason for blocking

Example log entry:
```
[2026-05-16T10:30:45] BLOCKED: rm -rf command
  Command: rm -rf /var/log/*
  Project: /home/user/myproject
```

## How It Works

The hook intercepts bash/shell tool calls and checks the command against dangerous patterns using regex. If a match is found:

1. The command is blocked
2. An entry is written to the log file
3. Claude receives a message explaining why the command was blocked

Normal commands pass through unaffected.

## Customization

Edit `block_destructive.py` to add or remove patterns:

```python
DANGEROUS_PATTERNS = [
    (r'\brm\s+-rf\b', "rm -rf command"),
    # Add your patterns here
]
```

## Testing

Test that blocking works:
```bash
echo '{"tool_name": "bash", "tool_input": {"command": "rm -rf /"}}' | python3 block_destructive.py
# Output: {"decision": "block", "message": "..."}
```

Test that normal commands pass:
```bash
echo '{"tool_name": "bash", "tool_input": {"command": "ls -la"}}' | python3 block_destructive.py
# Output: {"decision": "approve"}
```

## License

MIT
