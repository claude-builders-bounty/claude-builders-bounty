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

From this repository, install into any Claude Code project in two commands:

```bash
cd /path/to/your/project
python3 /path/to/claude-builders-bounty/skills/destructive-command-guard/install.py
```

The installer copies the hook to `.claude/hooks/destructive-command-guard.py`, makes it executable, and merges this Bash `PreToolUse` entry into `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/destructive-command-guard.py"
          }
        ]
      }
    ]
  }
}
```

Restart Claude Code and try running `rm -rf /tmp/test` to verify it blocks.

## Test

```bash
python3 test_guard.py

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

```json
{"command": "rm -rf /var/log", "project_path": "/home/user/myapp", "reason": "rm -rf: destructive recursive force delete", "timestamp": "2026-05-12T14:30:00Z"}
```

## Uninstall

Remove the hook entry from `.claude/settings.json` and delete `.claude/hooks/destructive-command-guard.py`.

## Coverage

This guard parses shell words for command-style invocations and uses SQL-aware checks for database statements. It handles case variations (`DROP TABLE`, `drop table`, `Drop Table`), common flag shortcuts (`rm -fr`, `git push -f`), long flags (`rm --recursive --force`), force-push refspecs (`git push origin +main`), nested shell commands (`bash -c 'rm -rf build'`), and SQL passed through common clients such as `psql -c`.

## License

MIT
