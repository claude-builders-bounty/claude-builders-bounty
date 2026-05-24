# Pre-Tool-Use Safety Hook

A Claude Code `pre-tool-use` hook that blocks dangerous bash commands before they execute.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use-hook.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use-hook.sh
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "preToolUse": ["bash ~/.claude/hooks/pre-tool-use-hook.sh"]
  }
}
```

## Blocked Commands

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Destructive SQL |
| `DROP DATABASE` | Destructive SQL |
| `git push --force` | Overwrites remote history |
| `TRUNCATE` | Deletes all rows |
| `DELETE FROM` (no WHERE) | Deletes all rows |
| `chmod 777` | Overly permissive |
| `curl \| sh` | Pipe to shell injection |
| `mkfs.*` | Format disk |
| `dd of=/dev/` | Write to device |

## How It Works

1. Intercepts every Bash tool call before execution
2. Checks the command against blocked patterns (regex)
3. If blocked: logs to `~/.claude/hooks/blocked.log` and returns exit code 2
4. If safe: exits 0 (command proceeds normally)

## Log Format

Every blocked attempt is logged with:
- Timestamp (ISO 8601)
- Current working directory
- The attempted command
- The reason for blocking

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Timestamp: 2025-01-15T10:30:00+00:00
Project:   /home/user/my-project
Command:   rm -rf node_modules
Reason:    Blocked: 'rm -rf' — recursive force delete is not allowed
```

## Testing

Run the test suite:

```bash
bash test-hook.sh
```

## Customization

Edit `pre-tool-use-hook.sh` to add/remove patterns. Each pattern follows:

```bash
if echo "$COMMAND" | grep -qE 'pattern'; then
    BLOCKED=true
    REASON="Blocked: explanation"
fi
```

## Requirements

- Claude Code (with hooks support)
- Bash 4+
- Python 3 (for JSON parsing)
