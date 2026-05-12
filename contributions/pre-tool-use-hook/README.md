# 🛡️ Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before execution, protecting your system from accidental destruction.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive.py ~/.claude/hooks/
cp hooks/settings.json ~/.claude/settings.json
```

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /` | Recursive force delete |
| `DROP TABLE` | `DROP TABLE users;` | SQL table destruction |
| `TRUNCATE` | `TRUNCATE orders` | SQL data wipe |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Unbounded SQL delete |
| `git push --force` | `git push --force origin main` | Force push overwrites history |
| `git reset --hard` | `git reset --hard HEAD~5` | Discards commits |
| `git clean -f` | `git clean -fd` | Removes untracked files |
| `mkfs` | `mkfs.ext4 /dev/sda1` | Formats filesystem |
| `dd` to device | `dd if=/dev/zero of=/dev/sda` | Overwrites disk |
| `chmod -R 777 /` | `chmod -R 777 /etc` | Destroys permissions |

## How It Works

1. Claude Code calls a bash/terminal tool
2. The hook intercepts the command via stdin (JSON event)
3. Regex patterns check for destructive commands
4. If matched: logs the attempt, returns a block message, exits non-zero
5. If safe: exits 0, command proceeds normally

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-13T00:30:00Z] BLOCKED: rm -rf: recursive force delete | Command: rm -rf / | Project: /home/user/myapp
```

Each entry includes:
- Timestamp (UTC)
- Reason for blocking
- Full attempted command
- Project path

## Customization

Edit `BLOCKED_PATTERNS` in `block_destructive.py` to add or remove patterns:

```python
BLOCKED_PATTERNS = [
    (r'your_regex_here', "Description of why it's blocked"),
    # ...
]
```

## Testing

```bash
# Test that it blocks rm -rf
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /"}}' | python3 ~/.claude/hooks/block_destructive.py
# Expected: exit code 1, JSON output with blocked=true

# Test that it allows safe commands
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"}}' | python3 ~/.claude/hooks/block_destructive.py
# Expected: exit code 0, no output
```

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)

## License

MIT
