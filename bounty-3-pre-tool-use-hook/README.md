# claude-guard

A Claude Code `pre-tool-use` hook that intercepts destructive bash and SQL commands before execution.

## Install (2 commands)

```bash
cp guard.sh ~/.claude/hooks/guard.sh
chmod +x ~/.claude/hooks/guard.sh
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "~/.claude/hooks/guard.sh" }]
      }
    ]
  }
}
```

## What it blocks

| Category | Patterns |
|----------|----------|
| **Filesystem** | `rm -rf`, `rm --recursive`, `rm --force`, `mkfs.*`, `dd of=/dev/*` |
| **Git** | `git push --force`, `git push -f`, `git reset --hard`, `git clean -fd` |
| **SQL** | `DROP TABLE/DATABASE/SCHEMA/INDEX`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| **System** | `chmod -R 777 /`, `chown -R ... /`, raw device writes |

## What it allows

- Normal `rm` (without `-rf`)
- `git push` (without `--force`)
- `DELETE FROM ... WHERE ...` (targeted deletes are fine)
- All other bash commands pass through untouched

## Logging

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-29T12:00:00Z] BLOCKED | reason: Recursive/force file deletion (rm -rf) | command: rm -rf / | path: /home/user/project
```

## How it works

1. Claude Code calls the hook before executing any `Bash` tool
2. The hook reads the command from stdin (JSON format)
3. Matches against a list of destructive regex patterns
4. If matched: logs the attempt, returns `exit 2` with a block reason
5. If safe: returns `exit 0` to allow execution

## Testing

```bash
# Should block:
echo '{"tool_input":{"command":"rm -rf /"}}' | bash guard.sh
echo '{"tool_input":{"command":"git push --force origin main"}}' | bash guard.sh
echo '{"tool_input":{"command":"DROP TABLE users;"}}' | bash guard.sh
echo '{"tool_input":{"command":"DELETE FROM users;"}}' | bash guard.sh

# Should allow:
echo '{"tool_input":{"command":"rm file.txt"}}' | bash guard.sh
echo '{"tool_input":{"command":"git push origin main"}}' | bash guard.sh
echo '{"tool_input":{"command":"DELETE FROM users WHERE id = 5;"}}' | bash guard.sh
```
