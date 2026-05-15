# Claude Code Hook: Block Destructive Bash Commands

A pre-tool-use hook that intercepts dangerous bash commands before they are executed by Claude Code.

## 💰 Bounty

This hook was created for the [claude-builders-bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) ($100 bounty).

## Installation (2 commands)

```bash
# 1. Copy the hook to your Claude Code hooks directory
mkdir -p ~/.claude/hooks && cp destructive_blocker_hook.py ~/.claude/hooks/

# 2. Add the hook configuration to your Claude Code settings
cat >> ~/.claude/settings.json << 'EOF'
{
  "hooks": {
    "pre_tool_use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_blocker_hook.py"
          }
        ]
      }
    ]
  }
}
EOF
```

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /var/data` | Recursive force delete can wipe entire directories |
| `DROP TABLE` | `DROP TABLE users;` | Irreversible SQL table destruction |
| `git push --force` | `git push --force origin main` | Overwrites remote history, loses commits |
| `TRUNCATE` | `TRUNCATE TABLE logs;` | Deletes all rows without recovery |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Deletes all rows unintentionally |

## How It Works

1. Claude Code sends JSON input via stdin before executing a Bash command
2. The hook parses the command and checks against blocked patterns
3. If matched, the command is **blocked** (exit code 2) and logged
4. A clear message is displayed explaining why the command was blocked
5. Safe commands pass through normally (exit code 0)

## Blocked Command Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (UTC ISO format)
- Attempted command
- Project path

Example log entry:
```
[2026-05-15T12:00:00+00:00] BLOCKED | cmd: rm -rf /tmp/important-data | path: /home/user/my-project
```

## Testing

```bash
# Test that safe commands pass
python3 destructive_blocker_hook.py <<< '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'
# Exit code: 0 (allowed)

# Test that destructive commands are blocked
python3 destructive_blocker_hook.py <<< '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp"}}'
# Exit code: 2 (blocked), message printed to stderr

# Test DELETE FROM without WHERE
python3 destructive_blocker_hook.py <<< '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM users;"}}'
# Exit code: 2 (blocked)

# Test DELETE FROM with WHERE (allowed)
python3 destructive_blocker_hook.py <<< '{"tool_name":"Bash","tool_input":{"command":"DELETE FROM users WHERE id = 5;"}}'
# Exit code: 0 (allowed)
```

## Sample Blocked Outputs

### Test 1: rm -rf
```
⛔ BLOCKED: The command 'rm -rf /var/data' was identified as potentially destructive.
Destructive commands (rm -rf, DROP TABLE, git push --force, TRUNCATE,
DELETE FROM without WHERE) are blocked to prevent accidental data loss.
If you really need to run this command, please confirm with the user first.
```

### Test 2: DROP TABLE
```
⛔ BLOCKED: The command 'DROP TABLE users;' was identified as potentially destructive.
```

### Test 3: git push --force
```
⛔ BLOCKED: The command 'git push --force origin main' was identified as potentially destructive.
```

## License

MIT