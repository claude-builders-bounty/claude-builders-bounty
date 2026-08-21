# Pre-Tool-Use Hook: Block Destructive Bash Commands

A lightweight, zero-dependency Python hook for Claude Code that intercepts
dangerous bash commands and SQL statements before execution.

## Blocked Patterns

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` / `rm -fr` | `rm -rf /tmp/project` | Recursive force deletion |
| `rm --recursive --force` | `rm --recursive --force dist/` | Recursive force deletion |
| `DROP TABLE` | `DROP TABLE users;` | Destructive SQL |
| `DROP DATABASE` | `DROP DATABASE prod;` | Destructive SQL |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | Table wipeout |
| `git push --force` | `git push origin main --force` | Overwrites remote history |
| `DELETE FROM` (no WHERE) | `DELETE FROM sessions;` | Unbounded deletion |

Safe commands like `rm single_file.txt`, `git push origin main`, and
`DELETE FROM users WHERE id = 5` pass through without interference.

## Installation (2 commands)

```bash
# 1. Copy the hook to Claude Code's hooks directory
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py

# 2. Register it in Claude Code settings
cat >> ~/.claude/settings.json << 'EOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "python3 ~/.claude/hooks/pre_tool_use.py"
      }
    ]
  }
}
EOF
```

If `~/.claude/settings.json` already exists, merge the `hooks` key into it
instead of overwriting.

## Logging

Every blocked command is appended to `~/.claude/hooks/blocked.log`:

```
[2026-08-21 14:30:05] BLOCKED | cmd: rm -rf /tmp/project | reason: rm -rf: recursive force deletion | path: /home/user/myproject
```

## Testing

```bash
python3 test_hook.py
```

## How It Works

Claude Code sends a JSON payload to stdin before each tool invocation.
The hook reads it, checks the `Bash` tool's `command` field against the
pattern list, and:

- **Exit 0** — command is allowed, Claude Code runs it normally.
- **Exit 2** — command is blocked; the stderr message is shown to Claude
  explaining why the command was blocked.
