# pre-tool-use-hook: Block Destructive Bash Commands

A [Claude Code pre-tool-use hook](https://docs.anthropic.com/claude-code/hooks) that intercepts dangerous bash commands before they execute.

## Installation

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre_tool_use.py https://raw.githubusercontent.com/wbobbynmworley/claude-builders-bounty/main/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py
```

Or copy `pre_tool_use.py` to your `~/.claude/hooks/` directory.

## What It Blocks

| Pattern | Danger |
|---------|--------|
| `rm -rf /` | Deletes root filesystem |
| `rm -rf $VAR` | Recursive variable expansion |
| `DROP TABLE` | Deletes database tables |
| `TRUNCATE TABLE` | Empties database tables |
| `DELETE FROM` (no WHERE) | Deletes all rows |
| `git push --force` / `-f` | Overwrites remote history |
| Fork bombs `:(){ :|:& };:` | Crashes the system |
| `mkfs.*` | Formats filesystems |
| `dd if=... of=/dev/` | Direct disk writes |
| `curl ... | sh` / `wget ... | sh` | Executes untrusted scripts |
| `shutdown -h` / `init 0` | System shutdown |

## Blocked Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-01T10:30:00] BLOCKED Bash: rm -rf / | project: /path/to/project
```

## Bypass

Confirm the command directly when prompted by Claude Code.

## Testing

```bash
# Should be blocked (exit code 1)
echo '{"name":"Bash","arguments":{"command":"rm -rf /"}}' | python pre_tool_use.py

# Should pass through (exit code 0)
echo '{"name":"Bash","arguments":{"command":"ls"}}' | python pre_tool_use.py
echo '{"name":"Bash","arguments":{"command":"git push origin main"}}' | python pre_tool_use.py
```

## Requirements

- Python 3.7+
- Claude Code (any recent version)

## License

MIT
