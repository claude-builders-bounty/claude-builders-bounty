# Claude Code — Destructive Bash Blocker Hook

A `PreToolUse` hook that intercepts dangerous bash commands before Claude executes them.

## What It Blocks

| Pattern | Reason |
|---|---|
| `rm -rf` / `rm -fr` | Recursive force delete |
| `DROP TABLE` | SQL table destruction |
| `git push --force` / `-f` | Rewrites remote git history |
| `TRUNCATE` | Removes all rows from a SQL table |
| `DELETE FROM <table>` (no WHERE) | Deletes every row in a table |

All blocked commands are logged to `~/.claude/hooks/blocked.log` with timestamp, reason, cwd, and command.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/block_destructive.py https://raw.githubusercontent.com/Nova17000/claude-builders-bounty/bounty-3-hook/hooks/block_destructive.py
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

## Log Format

```
2026-05-28T14:32:01 | BLOCKED | Recursive force delete (rm -rf) | cwd=/home/user/project | cmd='rm -rf /'
```

## Testing

```bash
echo '{"tool":"Bash","tool_input":{"command":"rm -rf /"}}' | python3 hooks/block_destructive.py
# → {"decision": "block", "reason": "🚫 Blocked: Recursive force delete ..."}

echo '{"tool":"Bash","tool_input":{"command":"ls -la"}}' | python3 hooks/block_destructive.py
# → (exit 0, no output — command allowed)
```
