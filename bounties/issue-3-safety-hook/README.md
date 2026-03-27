# Pre-Tool-Use Safety Hook

Blocks destructive bash commands before Claude Code executes them.

## Setup

```bash
# Option 1: Python hook (recommended)
cp guard.py ~/.claude/hooks/guard.py

# Option 2: Bash hook
cp guard.sh ~/.claude/hooks/guard.sh && chmod +x ~/.claude/hooks/guard.sh
```

Then add to your `~/.claude/settings.json` (or `.claude/settings.json` in your project):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/guard.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## What it blocks

| Pattern | Severity | Reason |
|---------|----------|--------|
| `rm -rf /` | Block | Recursive root deletion |
| `rm -rf <dir>` | Ask | Recursive directory deletion |
| `DROP TABLE` | Block | Irreversible table deletion |
| `DROP DATABASE` | Block | Irreversible database deletion |
| `TRUNCATE` | Block | Irreversible data wipe |
| `DELETE FROM` (no WHERE) | Block | Deletes all rows |
| `git push --force` | Ask | Rewrites remote history |
| `git reset --hard` | Ask | Discards uncommitted changes |
| `git clean -f` | Ask | Deletes untracked files |
| `git branch -D` | Ask | Force deletes branch |
| `chmod -R 777` | Block | World-writable all files |
| `dd of=/dev/` | Block | Disk overwrite |
| `mkfs.*` | Block | Filesystem format |
| `npm publish --force` | Block | Overwrites published package |
| `docker system prune -a` | Ask | Removes all unused data |

**Block** = always denied. **Ask** = user prompted to confirm.

## How it works

1. Claude Code sends a JSON payload to stdin before each Bash tool call
2. The hook parses the command and checks against destructive patterns
3. If matched, it logs to `~/.claude/hooks/blocked.log` and returns exit code 2
4. Claude receives the block reason and does not execute the command

## Log format

```
2026-03-27T23:15:00Z | /home/user/project | rm -rf /tmp/build | rm -rf — recursive directory deletion
```

## Requirements

- Python 3.6+ (for guard.py) OR bash + jq (for guard.sh)
- Claude Code hooks support
