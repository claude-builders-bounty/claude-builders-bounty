# Destructive Command Blocker — Claude Code Hook

A pre-tool-use hook that intercepts and blocks dangerous bash commands before Claude Code executes them.

## Install (2 commands)

```bash
cp guard-hook ~/.claude/hooks/guard-hook
chmod +x ~/.claude/hooks/guard-hook
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
            "command": "~/.claude/hooks/guard-hook"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

| Category | Patterns | Severity |
|----------|----------|----------|
| **Filesystem** | `rm -rf`, `mkfs`, `dd if=...of=/dev`, `chmod -R 777` | CRITICAL/HIGH |
| **Git** | `git push --force`, `git reset --hard`, `git clean -f`, `git checkout -- .` | HIGH/MEDIUM |
| **Database** | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without WHERE | CRITICAL/HIGH |
| **System** | `kill -9 -1`, `shutdown`, `reboot`, stop SSH | CRITICAL/HIGH |
| **Security** | `curl ... \| sh`, `wget ... \| bash` | MEDIUM |

## Logging

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
2026-04-10T01:00:00Z | CRITICAL | BLOCKED | Recursive force delete (rm -rf) | project=/home/user/app | cmd=rm -rf /
```

## How It Works

1. Claude Code calls the hook **before** executing any Bash command
2. The hook reads the command from stdin (JSON with `tool_name` and `command`)
3. Matches against 16 dangerous patterns using regex
4. If matched: logs the attempt, returns exit code 2 (blocks execution), shows explanation to Claude
5. If safe: exits 0 (allows execution)

## Safe Commands Pass Through

Normal commands like `ls`, `git status`, `npm install`, `cat file.txt` are never blocked. The hook only intercepts known-dangerous patterns.

## Requirements

- Bash 4+ (macOS/Linux/WSL)
- `grep` with `-P` (PCRE) or `-E` (extended regex)
- Claude Code with hooks support

## License

MIT
