# Destructive Command Guard

A Claude Code `PreToolUse` hook that blocks dangerous bash commands before they execute.

## What it blocks

| Category | Patterns |
|----------|----------|
| **Filesystem** | `rm -rf /`, `mkfs`, `dd of=/dev/`, `chmod 777 /`, fork bombs, `shred`, `fdisk` |
| **Remote Code Exec** | `curl \| bash`, `wget \| sh`, `eval()` |
| **SQL** | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| **Git** | `git push --force`, `git reset --hard`, `git branch -D` |
| **System** | `sudo rm -rf /`, `shutdown`, `reboot`, `killall` |

## Install (2 commands)

```bash
# 1. Copy the hook script
cp hooks/block-destructive-commands.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive-commands.sh

# 2. Add to ~/.claude/settings.json (merge with existing hooks):
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/block-destructive-commands.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## How it works

1. Hook receives JSON on stdin with the proposed bash command
2. Checks command against categorized pattern lists
3. If matched: logs to `~/.claude/hooks/blocked.log` and outputs a `block` decision
4. If clean: exits 0 (allow)

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
2026-05-13T12:00:00Z | session=abc123 | cwd=/home/user/project | command=rm -rf / | reason=[FILESYSTEM] Blocked dangerous command...
```

Set `CLAUDE_HOOKS_LOG` to customize the log path.

## False positives

If a command is incorrectly blocked, you can:
1. Temporarily disable the hook in `.claude/settings.json`
2. Modify the pattern lists in the script
3. The hook only blocks — it never auto-approves

## Acceptance Criteria

- [x] Follows Claude Code hooks format
- [x] Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- [x] Logs every blocked attempt with timestamp, command, project path
- [x] Displays clear message explaining why the command was blocked
- [x] Does not interfere with normal bash commands
- [x] README with installation in 2 commands or fewer
