# Claude Code Security Hook — Block Destructive Bash Commands

A `pre-tool-use` hook for Claude Code that **automatically blocks dangerous commands** before they execute — and logs every blocked attempt.

## Blocked patterns

| Pattern | Why |
|---------|-----|
| `rm -rf` | Destructive file deletion |
| `DROP TABLE` | Database schema destruction |
| `git push --force` / `git push -f` | Overwrites remote git history |
| `TRUNCATE` | Empties a database table |
| `DELETE FROM ... (no WHERE)` | Mass database record deletion |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.py
```

That's it. Claude Code will use it automatically when configured (see [docs](https://docs.anthropic.com/claude-code/hooks)).

## How it works

1. Claude Code calls the hook before any `bash` tool execution.
2. The hook reads the command from stdin (JSON or plain text).
3. If a dangerous pattern is found:
   - The command is **blocked** (hook exits with code `1`).
   - A clear message is printed to Claude explaining why.
   - The blocked attempt is logged to `~/.claude/hooks/blocked.log`.
4. Safe commands exit with code `0` and proceed normally.

## Log format (`~/.claude/hooks/blocked.log`)

Each blocked attempt is logged as JSON:

```json
{
  "timestamp": "2026-06-06T10:00:00.123456",
  "attempted_command": "rm -rf /var/log/old",
  "blocked_reason": "rm -rf (Destructive file deletion)",
  "project_path": "/home/user/my-project"
}
```

## Testing

Run the included test suite:

```bash
python test_pre_tool_use.py
```

All tests must pass before installation.
