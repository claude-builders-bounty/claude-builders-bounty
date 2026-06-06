# Pre-Tool-Use Hook — Block Destructive Bash Commands

A Claude Code pre-tool-use hook that intercepts dangerous bash commands before execution.

**Blocked patterns:**
- `rm -rf` / `rm -r /` / `rm -rf ~`
- `DROP TABLE` / `DROP DATABASE` / `TRUNCATE`
- `DELETE FROM` without WHERE clause
- `git push --force` / `git push -f` / `git reset --hard`
- `chmod -R 777` / `chown -R`
- `dd if=` / `mkfs.*` / raw disk writes
- Fork bomb patterns

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Setup (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hook.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

Reference the hook in your Claude Code config:
```json
{
  "hooks": {
    "PreToolUse": [{"command": "python3 ~/.claude/hooks/pre-tool-use"}]
  }
}
```
