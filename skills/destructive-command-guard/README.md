# Destructive Command Guard

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) `PreToolUse` hook that intercepts dangerous bash commands before they execute.

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive force delete destroys files irreversibly |
| `DROP TABLE / DATABASE / SCHEMA` | SQL commands that destroy database objects |
| `git push --force / -f / --force-with-lease` | Rewrites remote history, can lose others' work |
| `TRUNCATE / TRUNCATE TABLE` | Empties a table without filtering |
| `DELETE FROM ...` without `WHERE` | Deletes every row in a table |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with a timestamp, the attempted command, the project path, and the reason.

When a command is blocked, Claude receives a clear explanation of why, so it can suggest a safer alternative or ask you to bypass the hook manually.

All other bash commands pass through normally.

## Install

**1. Copy the hook scripts into your project:**

```bash
mkdir -p .claude/hooks
cp guard.py .claude/hooks/guard.py
chmod +x .claude/hooks/guard.py
```

**2. Add the hook configuration to `.claude/settings.json`:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/guard.py"]
          }
        ]
      }
    ]
  }
}
```

That's it. Restart Claude Code and try running `rm -rf /tmp/test` to verify it blocks.

## Test

```bash
# Quick test with sample JSON input
echo '{"tool_input":{"command":"rm -rf /var/log/app.log"},"cwd":"/home/user/project"}' | python3 guard.py
# Expected: JSON deny response + log entry in ~/.claude/hooks/blocked.log

echo '{"tool_input":{"command":"ls -la"},"cwd":"/home/user/project"}' | python3 guard.py
# Expected: no output, exit 0 (allowed)

echo '{"tool_input":{"command":"DELETE FROM users;"},"cwd":"/home/user/project"}' | python3 guard.py
# Expected: JSON deny response (no WHERE clause)

echo '{"tool_input":{"command":"DELETE FROM users WHERE id = 5;"},"cwd":"/home/user/project"}' | python3 guard.py
# Expected: no output, exit 0 (allowed, has WHERE clause)
```

## Log Format

Each blocked attempt appends a line to `~/.claude/hooks/blocked.log`:

```
2026-05-12T14:30:00Z | project=/home/user/myapp | reason=rm -rf: destructive recursive delete | command=rm -rf /var/log
```

## Uninstall

Remove the `"Bash"` matcher entry from `.claude/settings.json` and delete `.claude/hooks/guard.py`.

## Coverage

This guard uses five regex patterns covering command-style invocations (`rm -rf`, `git push --force`, plain SQL, and command-piped SQL). It handles case variations (`DROP TABLE`, `drop table`, `Drop Table`), multiline inputs (`DELETE FROM ... ;` without `WHERE` on any line), and common flag shortcuts (`rm -fr`, `git push -f`).

## License

MIT