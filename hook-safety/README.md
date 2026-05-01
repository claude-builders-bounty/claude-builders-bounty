# Pre-Tool-Use Hook: Dangerous Command Interceptor 🛡️

A Claude Code pre-tool-use hook that blocks destructive bash commands before they execute — including `rm -rf`, `DROP TABLE`, `TRUNCATE`, `DELETE FROM` (no WHERE), `git push --force`, and more.

## Install (2 commands)

```bash
cp hook-safety.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/hook-safety.py
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre_tool_use": [
      {
        "matcher": "Bash",
        "hook": "python3 ~/.claude/hooks/hook-safety.py"
      }
    ]
  }
}
```

## What It Blocks

| Severity | Patterns |
|----------|----------|
| 🚨 Critical | `rm -rf /`, `mkfs`, `dd if=/dev/zero`, fork bombs, `shutdown`, `DROP TABLE`, `TRUNCATE TABLE`, `DELETE FROM` (no WHERE), `DROP DATABASE` |
| ⚠️ High | `curl \| sh`, reverse shells, `chmod 777 /`, `iptables -F`, `git push --force` |
| ⚡ Medium | `git reset --hard`, `git clean -f`, `npm publish` |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-01 10:23:45] SEVERITY=critical RULE=DROP TABLE — permanently deletes a table PROJECT=/home/user/myapp
  COMMAND: DROP TABLE users;
```

Each entry includes:
- **Timestamp** — when the command was blocked
- **Severity** — critical / high / medium
- **Rule** — which pattern matched
- **Project** — the working directory
- **Command** — the full command that was blocked

## How It Works

```
Claude Code wants to run a command
        ↓
Hook receives JSON on stdin
        ↓
Extract command string
        ↓
Match against 30+ dangerous patterns
        ↓
  ┌─────┴─────┐
  │ Safe       │ Dangerous
  ↓            ↓
Exit 0      Log to blocked.log
(no output)  + Print block JSON
             + Exit 0
```

## Customization

### Add Your Own Patterns

Edit the `DANGEROUS_PATTERNS` list:

```python
{
    "pattern": r"\bmy-dangerous-command\b",
    "description": "Custom dangerous command",
    "severity": "high",
}
```

### Adjust Severity Thresholds

```python
BLOCK_SEVERITIES = {"critical", "high"}   # These get blocked
WARN_SEVERITIES = {"medium"}              # These get warnings
```

## Limitations

- Matches against raw command string (not parsed shell AST)
- Can be bypassed via obfuscation (base64, variables, etc.)
- Safety net, not a security boundary
- Cannot catch every possible dangerous pattern

## License

MIT
