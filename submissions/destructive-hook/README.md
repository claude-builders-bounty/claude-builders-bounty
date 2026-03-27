# Destructive Command Blocker Hook

Pre-tool-use hook that blocks dangerous bash commands before execution.

## Install (2 commands)

```bash
cp block-destructive.sh ~/.claude/hooks/block-destructive.sh
chmod +x ~/.claude/hooks/block-destructive.sh
```

Then add to your `.claude/settings.json` (or merge with existing):

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/block-destructive.sh",
        "timeout": 5
      }]
    }]
  }
}
```

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf /`, `rm -rf ~`, `rm -rf .` | Recursive deletion of critical paths |
| `DROP TABLE`, `DROP DATABASE` | Database destruction |
| `TRUNCATE` | Table data wipe |
| `DELETE FROM` without `WHERE` | Deletes all rows |
| `git push --force`, `git push -f` | Force push overwrites history |
| `git reset --hard` | Discards uncommitted changes |
| `> /dev/sda`, `mkfs.`, `dd if=/dev/zero` | Disk destruction |
| `chmod -R 777 /` | Security compromise |
| Fork bomb pattern | System crash |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-27T02:30:00Z] BLOCKED: 'rm -rf /' in /home/user/project
[2026-03-27T02:31:00Z] BLOCKED: 'DELETE FROM users' (DELETE without WHERE) in /home/user/project
```

## Normal Commands

The hook does NOT block normal commands like `rm file.txt`, `git push`, `DELETE FROM users WHERE id = 5`, etc.
