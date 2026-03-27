# Destructive Command Guard

Claude Code pre-tool-use hook that intercepts dangerous bash commands before execution.

## Blocked patterns

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /`, `rm -rf .` |
| `DROP TABLE` | `DROP TABLE users` |
| `TRUNCATE` | `TRUNCATE TABLE orders` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users` |
| `git push --force` | `git push --force`, `git push -f` |

Safe variants like `rm file.txt`, `DELETE FROM users WHERE id=1`, and `git push --force-with-lease` are not blocked.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/guard.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/guard.sh
```

Add to `~/.claude/settings.json` (merge with existing hooks if any):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/guard.sh"
          }
        ]
      }
    ]
  }
}
```

## Log

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-27T23:45:00+03:00] BLOCKED | rm -rf: recursive force delete | cmd: rm -rf / | project: /home/user/myproject
```

## Limitations

- Indirect execution is not caught: `bash -c "rm -rf /"`, `eval`, `find -exec`, heredocs
- Pattern matching is string-based — obfuscated commands can bypass detection
- This is a safety net, not a security boundary

## Requires

- `jq`
