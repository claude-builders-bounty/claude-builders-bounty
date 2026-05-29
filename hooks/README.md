# Block Destructive Commands Hook

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they are executed.

## Features

- **Blocks dangerous patterns**: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- **Logging**: Every blocked attempt is logged to `~/.claude/hooks/blocked.log`
- **Clear messages**: Claude receives a clear explanation of why the command was blocked
- **Safe by default**: Does not interfere with normal bash commands

## Installation (2 commands)

```bash
cp hooks/block-destructive.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.sh
```

## How It Works

When Claude Code attempts to run a bash command, this hook:

1. Intercepts the command before execution
2. Checks for dangerous patterns using regex matching
3. If a dangerous pattern is found:
   - Logs the attempt to `~/.claude/hooks/blocked.log`
   - Returns a clear error message to Claude
   - Blocks the command from executing
4. If no dangerous pattern is found:
   - Allows the command to execute normally

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force deletion cannot be undone |
| `DROP TABLE` | Permanently deletes database tables |
| `git push --force` | Overwrites remote history, can cause data loss |
| `TRUNCATE TABLE` | Removes all rows from a table |
| `DELETE FROM` (no WHERE) | Deletes all rows without filtering |
| `mkfs.*` | Formats filesystem, erasing all data |
| `dd of=` | Direct disk writes can overwrite data |
| `chmod 777` | Overly permissive permissions (security risk) |

## Log Format

Each blocked attempt is logged with:
- Timestamp
- Attempted command
- Reason for blocking
- Current project path

Example log entry:
```
[2026-05-29 10:30:45] BLOCKED: rm -rf /tmp/test | Reason: rm -rf: Recursive force deletion blocked | Project: /home/user/project
```

## Customization

To add or remove patterns, edit the `check_command` function in `block-destructive.sh`. Each pattern follows this structure:

```bash
# Pattern N: Description
if echo "$cmd" | grep -qiE 'PATTERN'; then
    log_blocked "$cmd" "PATTERN: Description"
    echo "BLOCKED: Explanation message"
    exit 1
fi
```

## Testing

Test the hook by running commands that should be blocked:

```bash
# Should be blocked
echo "rm -rf /tmp/test" | ~/.claude/hooks/block-destructive.sh
echo "DROP TABLE users" | ~/.claude/hooks/block-destructive.sh
echo "git push --force origin main" | ~/.claude/hooks/block-destructive.sh

# Should be allowed
echo "ls -la" | ~/.claude/hooks/block-destructive.sh
echo "cat file.txt" | ~/.claude/hooks/block-destructive.sh
```

## Requirements

- Bash 4.0 or higher
- Claude Code with hooks support

## License

MIT
