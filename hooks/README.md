# Claude Code Destructive Command Guard

A `pre-tool-use` hook for Claude Code that intercepts and blocks destructive bash commands before they execute.

## Blocked Commands

| Command | Why |
|---------|-----|
| `rm -rf` | Prevents recursive force deletion |
| `git push --force` / `-f` | Prevents overwriting remote history |
| `DROP TABLE` | Prevents schema destruction |
| `TRUNCATE` | Prevents mass data deletion |
| `DELETE FROM` (no WHERE) | Prevents wiping entire tables |

## Install (2 commands)

```bash
cp guard-hook.sh ~/.claude/hooks/guard-hook.sh && chmod +x ~/.claude/hooks/guard-hook.sh
```

Then add to your `.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "command": "~/.claude/hooks/guard-hook.sh"
      }
    ]
  }
}
```

## How It Works

1. Claude Code calls a Bash tool → the hook receives the command as JSON on stdin
2. The hook checks against the destructive command patterns
3. If matched: logs to `~/.claude/hooks/blocked.log` and exits with code 2 (blocks execution)
4. If safe: exits 0 (allows execution)

## Log Format

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
2026-03-29T14:30:00Z | BLOCKED | rm -rf / | /home/user/project
```

Fields: `timestamp | BLOCKED | attempted_command | project_path`

## Normal Commands

The hook does **not** interfere with safe commands like `rm file.txt`, `git push`, `DELETE FROM users WHERE id = 5`, or any non-Bash tool calls.
