# Pre-Tool-Use Security Hook for Claude Code

A Python-based hook that intercepts dangerous bash commands before they are executed by Claude Code. Blocks recursive deletes, DROP statements, force pushes, and other destructive operations.

## What It Blocks

| Pattern | Example | Why |
|---|---|---|
| `rm -rf` (any flag combo) | `rm -rf /tmp/foo` | Recursive force delete |
| `DROP TABLE/DATABASE` | `DROP TABLE users` | Destructive DDL |
| `git push --force` / `-f` | `git push --force` | Force push rewrites history |
| `TRUNCATE TABLE` | `TRUNCATE TABLE logs` | Deletes all rows |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Deletes all rows |

## What It Does NOT Block

- `rm file.txt` (specific file, no recursive)
- `git push` (normal push)
- `DELETE FROM table WHERE id=1` (with WHERE)
- All non-destructive bash commands

## Installation (2 commands)

```bash
# 1. Create hooks directory and copy the file
mkdir -p ~/.claude/hooks && cp pre_tool_use.py ~/.claude/hooks/

# 2. Register the hook in Claude Code settings
# Add this to ~/.claude/settings.json:
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use.py"
          }
        ]
      }
    ]
  }
}
```

## How It Works

1. Claude Code calls the hook before executing any Bash tool
2. Hook receives JSON with the command
3. Hook checks against 5 regex patterns
4. If matched: logs to `~/.claude/hooks/blocked.log`, exits 2 (blocks command)
5. If not matched: exits 0 (allows command)

## Log Format

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-03T18:45:00+00:00] BLOCKED
  Project: /home/user/project
  Reason:  rm -rf: recursive force delete
  Command: rm -rf /tmp/build
--------------------------------------------------------------------------------
```

## Testing

Test the hook manually:

```bash
# Should block (exit 2)
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/foo"}}' | python3 pre_tool_use.py

# Should allow (exit 0)
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 pre_tool_use.py
```

## Why Python?

- Zero dependencies (just stdlib)
- Cross-platform (Linux, macOS)
- Easy to extend (add patterns in `DANGEROUS_PATTERNS` list)
- Easier to test than bash

## Customization

Add new dangerous patterns by editing `DANGEROUS_PATTERNS`:

```python
DANGEROUS_PATTERNS = [
    # Add your custom pattern
    (r"\bcurl\s+.*\|\s*bash\b", "curl piped to bash: potential RCE"),
    (r"\bsudo\s+rm\b", "sudo rm: privileged delete"),
]
```

## Compatibility

- Python 3.6+
- Claude Code (any version with hooks support)
- Linux, macOS (Windows requires WSL or git-bash)

## License

MIT
