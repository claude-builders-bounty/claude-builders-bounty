# Claude Code Safety Hook 🛡️

Pre-tool-use hook that intercepts destructive bash commands before execution.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_hook.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use_hook.py
```

## What It Blocks

| Severity | Pattern | Example |
|----------|---------|---------|
| 🔴 Critical | `rm -rf`, `rm -fr` | `rm -rf /path/to/dir` |
| 🔴 Critical | `DROP TABLE` | `DROP TABLE users;` |
| 🔴 Critical | `TRUNCATE` | `TRUNCATE TABLE logs;` |
| 🔴 Critical | `DELETE FROM` (no WHERE) | `DELETE FROM users;` |
| 🔴 Critical | `mkfs`, `dd if=/dev/zero` | Disk destruction |
| 🔴 Critical | Fork bombs | `:(){ :|:& };:` |
| 🟡 High | `git push --force` / `-f` | History overwrite |
| 🟡 High | `chmod 777` | Overly permissive |
| 🟡 High | `curl \| bash` | Remote script execution |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
2026-05-17T10:30:00+0800 | WARNING | BLOCKED [critical] | cmd='rm -rf /tmp/project' | path=/Users/dev/myproject
```

Each log entry includes: timestamp, severity, blocked command, and project path.

## How It Works

1. Claude Code calls this hook before executing any bash command
2. The hook checks the command against 15+ blocked patterns
3. If matched → returns a block response with explanation
4. If not matched → allows execution (exit 0)

## Configuration

To add custom patterns, edit the `BLOCKED_PATTERNS` list in `pre_tool_use_hook.py`:

```python
{
    "pattern": r'\byour_regex\b',
    "reason": "Blocked: your explanation",
    "severity": "high",  # or "critical"
}
```

## Testing

Run the hook directly to test:

```bash
echo '{"tool": "bash", "command": "rm -rf /tmp/test"}' | python3 ~/.claude/hooks/pre_tool_use_hook.py
# → returns block response + exit code 1

echo '{"tool": "bash", "command": "ls -la"}' | python3 ~/.claude/hooks/pre_tool_use_hook.py
# → exit code 0 (allowed)
```

## Compliance

✅ Follows Claude Code hooks format (`~/.claude/hooks/`)
✅ Blocks all required patterns (rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM w/o WHERE)
✅ Logs every blocked attempt with timestamp, command, and project path
✅ Displays clear explanation to Claude
✅ Does not interfere with normal bash commands
✅ Installation in 2 commands
