# Bash Safety Hook — Block Destructive Commands in Claude Code

A pre-tool-use hook for Claude Code that intercepts and blocks destructive bash commands before they execute.

## Setup (2 steps)

1. Copy the hook script to your project:
   ```bash
   mkdir -p .claude/hooks
   cp hooks/bash-safety/bash-safety-hook.sh .claude/hooks/
   chmod +x .claude/hooks/bash-safety-hook.sh
   ```

2. Register it in `.claude/settings.json`:
   ```json
   {
     "hooks": {
       "pre_tool_use": [
         {
           "matcher": "Bash",
           "command": ".claude/hooks/bash-safety-hook.sh"
         }
       ]
     }
   }
   ```

## What It Blocks

### File Operations
| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /` | Recursive force delete |
| `rm --force` | `rm --force important.db` | Force delete without confirmation |
| `dd of=/dev/` | `dd if=/dev/zero of=/dev/sda` | Direct disk write |
| `mkfs.` | `mkfs.ext4 /dev/sda1` | Filesystem format |

### Git Operations
| Pattern | Example | Why |
|---------|---------|-----|
| `git push --force` | `git push -f origin main` | Overwrites remote history |
| `git reset --hard` | `git reset --hard HEAD~5` | Discards uncommitted changes |
| `git clean -f` | `git clean -fd` | Removes untracked files permanently |
| `git checkout -- .` | `git checkout -- .` | Discards all unstaged changes |
| `git branch -D` | `git branch -D feature` | Force-deletes without merge check |
| `git stash drop` | `git stash drop stash@{0}` | Permanently removes stash |

### Database Operations
| Pattern | Example | Why |
|---------|---------|-----|
| `DROP TABLE` | `DROP TABLE users;` | Destroys table and data |
| `TRUNCATE TABLE` | `TRUNCATE TABLE logs;` | Removes all rows |
| `DELETE FROM x;` | `DELETE FROM users;` | Deletes all rows (no WHERE) |

### System & Security
| Pattern | Example | Why |
|---------|---------|-----|
| `kill -9` | `kill -9 1234` | Forceful process termination |
| `chmod 777 /` | `chmod -R 777 /var` | Opens system files to everyone |
| `cat .env` | `cat .env` | Exposes secrets |
| `curl \| sh` | `curl url \| bash` | Remote code execution risk |

## How It Works

The hook receives a JSON event from Claude Code's hook system on stdin:
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf /"
  }
}
```

It checks the command against destructive patterns and returns either:
- `{"decision": "approve"}` — command is safe, proceed
- `{"decision": "block", "reason": "..."}` — command is blocked with explanation

## Customization

Add your own patterns by adding blocks to `bash-safety-hook.sh`:
```bash
if echo "$CMD_LOWER" | grep -qP 'your-pattern-here'; then
  BLOCKED=true
  REASON="Blocked: Your custom reason"
fi
```

## Dependencies

- `jq` (for JSON parsing)
- `bash` 4.0+
- `grep` with `-P` (Perl regex) support

## License

MIT
