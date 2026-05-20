# 🛡️ Destructive Command Guard

A **Claude Code PreToolUse hook** that intercepts dangerous bash/shell commands
before they execute.

> 💰 Built for [BOUNTY #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) ($100)

## Installation

```bash
mkdir -p ~/.claude/hooks && cp destructive-guard/pre-tool-use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.py
```

Then add to your `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre-tool-use.py"
          }
        ]
      }
    ]
  }
}
```

That's it — **2 steps**: copy the script, add the config.

## What It Blocks

| Category | Patterns | Example |
|----------|----------|---------|
| File Deletion | `rm -rf`, `rm --no-preserve-root` | `rm -rf /` |
| Database | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE` | `DROP TABLE users;` |
| Git | `git push --force` / `--force-with-lease` | `git push --force origin main` |
| Permissions | `chmod 777` | `chmod 777 /var/www` |
| Fork Bombs | `:(){ :\|:& };:` | `:(){ :\|:& };:` |
| Disk Writes | `dd` to `/dev/sd*`, `mkfs`, redirect to `/dev/` | `dd if=/dev/zero of=/dev/sda` |
| Windows | `format C:`, `del /f /s`, `rmdir /s` | `del /f /s C:\*` |

## Safe Overlaps (Auto-allowed)

Some commands that look dangerous are actually common in build/CI scripts
and are automatically allowed:

- `rm -rf node_modules` / `__pycache__` / `.next` / `dist` / `build`
- `rm *.o` / `*.obj` / `*.exe`

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-20T10:30:00Z] BLOCKED | project=/home/user/myapp | patterns=[rm -rf] | command="rm -rf /tmp/build"
```

## Testing

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf --no-preserve-root /"},"project_path":"/test"}' | python3 pre-tool-use.py
# Expected: JSON output with permissionDecision: "deny"

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"project_path":"/test"}' | python3 pre-tool-use.py
# Expected: exit 0 (no output)
```

## Requirements

- Python 3.6+
- No external dependencies (stdlib only)
