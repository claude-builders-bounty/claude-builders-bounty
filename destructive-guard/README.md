# Destructive Command Guard — Pre-Tool-Use Hook

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use-guard.py ~/.claude/hooks/pre-tool-use-guard.py
```

Then add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use-guard.py"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

| Pattern           | Reason                              |
|-------------------|-------------------------------------|
| `rm -rf`          | Recursive force delete              |
| `DROP TABLE`      | Irreversible schema deletion        |
| `git push --force`| Overwrite remote history            |
| `TRUNCATE`        | Irreversible data wipe              |
| `DELETE FROM` (no WHERE) | Full table wipe              |
| `chmod -R 777`    | World-writable exposure             |
| `fork bomb (:(){})` | System DoS                       |
| `dd if=... of=/dev/` | Disk destruction                |
| `mkfs.*`          | Filesystem creation = data loss     |
| `git reset --hard`| Irreversible working tree reset     |

## Log Location

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (ISO 8601)
- Attempted command
- Block reason
- Working directory