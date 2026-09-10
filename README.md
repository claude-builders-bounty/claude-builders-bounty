# Block Destructive Commands — Claude Code Hook

A lightweight pre-tool-use hook that intercepts dangerous bash commands before they execute.

## Install (2 commands)

```bash
cp block_destructive.py ~/.claude/hooks/block_destructive.py && chmod +x ~/.claude/hooks/block_destructive.py
cp settings.json ~/.claude/settings.json  # or merge into existing file
```

## What it blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /tmp/build` |
| `DROP TABLE` | `DROP TABLE users` |
| `TRUNCATE` | `TRUNCATE TABLE logs` |
| `DELETE` without `WHERE` | `DELETE FROM sessions` |
| `git push --force` | `git push --force origin main` |
| `mkfs` | `mkfs.ext4 /dev/sda1` |
| `dd` to device | `dd if=file of=/dev/sdb` |

## What it allows

All non-destructive commands pass through unchanged: `ls`, `cat`, `git status`, `git push`, `git push --force-with-lease`, `rm` (single file), `DELETE FROM table WHERE id=1`, etc.

## Triple-signal blocking

When a destructive command is detected, the hook fires all three signals simultaneously:

1. **stdout JSON** — `{"hookSpecificOutput": {"permissionDecision": "deny", ...}, "decision": "block", "reason": "..."}`
2. **stderr** — reason text printed to stderr
3. **exit code 2** — signals block to Claude Code

## Logs

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-09-10T12:00:00Z] BLOCKED | project=/home/user/repo | command=rm -rf node_modules
```

## How it works

1. Claude Code calls the hook before every `Bash` tool use
2. The hook reads the command from stdin JSON
3. If the command matches a blocked pattern, it returns deny + stderr + exit 2
4. If safe, it exits 0 and Claude proceeds normally

## Testing

31 test cases covering blocked patterns, allowed commands, and edge cases. Run with:

```bash
python3 test_hook.py
```
