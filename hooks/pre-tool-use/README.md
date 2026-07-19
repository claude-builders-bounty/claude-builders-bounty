# Pre-Tool-Use Hook: Block Destructive Bash Commands

Prevents Claude Code from executing destructive bash commands like `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause.

## Installation

```bash
# 1. Create hooks directory
mkdir -p ~/.claude/hooks

# 2. Copy the hook (choose bash or python)
cp hooks/pre-tool-use/block-destructive.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py

# 3. Add to Claude Code settings (~/.claude/settings.json)
```

Add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use.py"
          }
        ]
      }
    ]
  }
}
```

### Bash version (alternative)

```bash
cp hooks/pre-tool-use/block-destructive.sh ~/.claude/hooks/pre-tool-use.sh
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/pre-tool-use.sh"
          }
        ]
      }
    ]
  }
}
```

## Blocked Patterns

| Pattern | Reason |
|--------|--------|
| `rm -rf` / `rm --recursive` | Recursively deletes files/directories |
| `DROP TABLE` | Destroys database tables |
| `DROP DATABASE` | Destroys entire databases |
| `TRUNCATE` | Empties tables without logging |
| `DELETE FROM` without `WHERE` | Deletes all rows in table |
| `git push --force` / `git push -f` | Overwrites remote history |
| `git reset --hard` | Discards all uncommitted changes |
| `git clean -df` | Removes untracked files/dirs |
| `chmod -R 777` | Makes everything world-writable |
| `chown -R` | Recursively changes ownership |
| `mkfs` | Formats a filesystem |
| `dd ... of=/dev/` | Writes directly to disk device |
| `> /dev/sd*` | Overwrites raw disk |
| Fork bomb `:(){...};:` | Denial of service |
| `shutdown` / `reboot` / `halt` | Powers off/restarts machine |
| `killall` | Kills all processes by name |
| `pkill -9` | Force-kills processes |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` as JSON:

```json
{"timestamp":"2026-07-19T12:00:00Z","command":"rm -rf /","reason":"rm -rf: recursively deletes files/directories","project_path":"/home/user/myproject"}
```

## How It Works

1. Claude Code calls a bash tool
2. The hook receives JSON on stdin: `{"tool_name": "Bash", "tool_input": {"command": "..."}}`
3. The hook checks the command against destructive patterns
4. If matched, it outputs `{"decision": "block", "reason": "..."}` and Claude receives an explanation
5. If safe, it exits silently and the command proceeds normally

## Testing

```bash
# Test with a destructive command (should be blocked)
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' | python3 ~/.claude/hooks/pre-tool-use.py

# Test with a safe command (should pass)
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 ~/.claude/hooks/pre-tool-use.py

# Check the log
cat ~/.claude/hooks/blocked.log
```
