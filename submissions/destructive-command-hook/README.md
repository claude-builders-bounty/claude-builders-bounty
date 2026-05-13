# Pre-Tool-Use Hook: Block Destructive Bash Commands

> **Bounty #3** — $100 HOOK: Pre-tool-use hook that blocks destructive bash commands

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## Installation (2 Commands)

```bash
# 1. Copy hook to Claude Code hooks directory
mkdir -p ~/.claude/hooks && cp pre-tool-use-block-destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.py

# 2. Add to Claude Code settings (or merge with existing config)
cat >> ~/.claude/settings.json << 'EOF'
{
  "hooks": {
    "preToolUse": [
      {
        "matcher": "bash|shell",
        "command": "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py",
        "timeout": 5000
      }
    ]
  }
}
EOF
```

> **Note:** If you already have a `settings.json`, merge the `hooks` section carefully rather than overwriting.

## What It Blocks

| Pattern | Example | Reason |
|---|---|---|
| `rm -rf` / `rm -fr` | `rm -rf /tmp/test` | Recursive force delete |
| `DROP TABLE` | `DROP TABLE users;` | Destroys database table |
| `DROP DATABASE` | `DROP DATABASE production;` | Destroys entire database |
| `TRUNCATE` | `TRUNCATE TABLE logs;` | Deletes all rows |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Deletes all rows |
| `git push --force` | `git push --force origin main` | Overwrites remote history |
| `git push -f` | `git push -f` | Overwrites remote history |
| Fork bombs | `:(){ :|:& };:` | Crashes the system |
| `mkfs` | `mkfs.ext4 /dev/sda1` | Formats filesystem |
| `dd of=/dev/` | `dd if=/dev/zero of=/dev/sda` | Destroys disk data |
| `shutdown` / `reboot` / `halt` | `shutdown now` | System control |

## Features

- ✅ Follows Claude Code hooks format (`pre-tool-use` via `~/.claude/settings.json`)
- ✅ Blocks all required patterns: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- ✅ Logs every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
- ✅ Displays clear message to Claude explaining why the command was blocked
- ✅ Does not interfere with normal bash commands
- ✅ Installation in 2 commands or fewer
- ✅ Zero external dependencies (Python 3 standard library only)

## Log Format

Blocked attempts are logged as JSON lines to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-05-14T04:10:00Z", "command": "rm -rf /var/log", "reason": "rm -rf or rm -fr: recursive force delete", "project_path": "/home/user/myproject"}
```

## How It Works

1. Claude Code calls the hook before executing any `bash` or `shell` tool
2. The hook reads the command from stdin (JSON format per Claude Code hooks spec)
3. It matches the command against a list of dangerous patterns
4. If matched: logs the attempt and returns a `block` decision with an explanation
5. If not matched: exits silently, allowing the command to proceed

## Testing

```bash
# Test the hook directly
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /tmp/test"},"project_path":"/home/user/project"}' | python3 pre-tool-use-block-destructive.py

# Expected output:
# {"decision": "block", "reason": "🚫 Command blocked by security hook: ..."}

# Test that normal commands pass through
echo '{"tool_name":"bash","tool_input":{"command":"ls -la"},"project_path":"/home/user/project"}' | python3 pre-tool-use-block-destructive.py

# Expected: no output (command allowed)
```

## Files

| File | Description |
|---|---|
| `pre-tool-use-block-destructive.py` | The hook script |
| `README.md` | This file |

## License

MIT
