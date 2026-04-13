# Destructive Command Blocker — Claude Code Pre-Tool-Use Hook

A production-ready Claude Code hook that intercepts and blocks dangerous bash commands before they execute, protecting your system from accidental data loss.

## What It Does

This hook runs **before** every `Bash` tool invocation in Claude Code. It pattern-matches the command against a curated list of destructive operations and:

- **Blocks** the command (exit code 2) if it matches a dangerous pattern
- **Logs** every blocked attempt with timestamp, command, and working directory to `~/.claude/hooks/blocked.log`
- **Explains** to Claude why the command was blocked via structured JSON output
- **Allows** safe commands to pass through with zero overhead (exit code 0)

## Blocked Patterns

| Pattern | Why It's Dangerous |
|---|---|
| `rm -rf` | Recursive force deletion — can wipe entire directory trees |
| `DROP TABLE` | Permanently removes database tables and all data |
| `TRUNCATE` | Removes all rows from a table without row-level logging |
| `DELETE FROM ... ;` (no WHERE) | Deletes every row in a table |
| `git push --force` / `git push -f` | Rewrites remote history, causes data loss for collaborators |
| `git reset --hard` | Discards all uncommitted changes permanently |
| `mkfs.` | Formats a filesystem partition |
| `dd if=` | Raw disk copy that can overwrite partitions or devices |
| `:(){ :\|:& };:` | Fork bomb — crashes the system via infinite process spawning |

## Installation (2 commands)

```bash
# 1. Copy the hook into place
cp hook.sh ~/.claude/hooks/pre-tool-use-destructive-guard.sh

# 2. Register it in your Claude Code settings
cat >> ~/.claude/settings.json << 'EOF'
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hook": "~/.claude/hooks/pre-tool-use-destructive-guard.sh"
      }
    ]
  }
}
EOF
```

> **Note**: If `~/.claude/settings.json` already exists, merge the `hooks` key into your existing configuration instead of appending.

## How It Works

1. Claude Code invokes the hook before each tool use, passing JSON on **stdin**:
   ```json
   {
     "tool_name": "Bash",
     "tool_input": {
       "command": "rm -rf /"
     }
   }
   ```
2. The hook extracts `tool_name` — if it's not `Bash`, it exits `0` (allow) immediately.
3. It extracts the `command` string and tests it against each destructive regex pattern.
4. **If a match is found**:
   - Logs the attempt to `~/.claude/hooks/blocked.log`
   - Outputs a JSON block decision: `{"decision": "block", "reason": "..."}`
   - Exits with code `2` (Claude Code's "block" convention)
5. **If no match**: exits with code `0` (allow).

## Examples

### Blocked Commands

```bash
rm -rf /                        # Blocked: recursive force delete
rm -rf .                        # Blocked: recursive force delete
rm -rfi some_dir                # Blocked: -rf flags present
git push --force origin main    # Blocked: force push
git push -f origin main         # Blocked: force push shorthand
git reset --hard HEAD~3         # Blocked: hard reset
DROP TABLE users;               # Blocked: drops table
DELETE FROM users;              # Blocked: DELETE without WHERE
TRUNCATE orders;                # Blocked: truncates table
dd if=/dev/zero of=/dev/sda     # Blocked: raw disk write
mkfs.ext4 /dev/sda1             # Blocked: formats partition
:(){ :|:& };:                   # Blocked: fork bomb
```

### Allowed Commands (no false positives)

```bash
rm file.txt                     # Allowed: no -rf flags
rm -f single_file.log           # Allowed: force on single file, no recursive
git push origin main            # Allowed: normal push
git push                        # Allowed: normal push
git reset --soft HEAD~1         # Allowed: soft reset preserves changes
git reset HEAD file.txt         # Allowed: unstage, not --hard
DELETE FROM users WHERE id = 5; # Allowed: has WHERE clause
ls -rf                          # Allowed: ls, not rm
echo "rm -rf"                   # Allowed: just echoing text (*)
grep "DROP TABLE" schema.sql    # Allowed: searching, not executing (*)
```

> (*) String matching has inherent limits. Commands that merely *mention* a pattern inside a string argument may still trigger the guard. This is the safe default — it's better to block a grep that mentions `rm -rf` than to miss a real `rm -rf`.

## Log Format

Each blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
[2026-04-13T10:30:00Z] BLOCKED | command: rm -rf / | reason: rm -rf: recursive force deletion can destroy entire directory trees | cwd: /home/user/project
```

## Requirements

- Bash 4.0+ (macOS, Linux, WSL)
- `grep` with `-E` (extended regex) support (standard on all platforms)
- No external dependencies — pure bash

## License

MIT
