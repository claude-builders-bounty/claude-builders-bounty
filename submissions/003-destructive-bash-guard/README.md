# Destructive Bash Guard

A Claude Code `PreToolUse` hook that intercepts and blocks dangerous shell commands before execution.

## Blocked Patterns

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -fr` / `rm -r -f` | Mass file deletion |
| `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` | Schema destruction |
| `git push --force` / `git push -f` | Remote history overwrite |
| `TRUNCATE [TABLE]` | Data destruction |
| `DELETE FROM <table>` without `WHERE` | Mass data deletion |
| `chmod 777` | World-writable permissions |
| fork bomb `:(){ :|:& };:` | System DoS |

## Install

```bash
cp guardian ~/.claude/hooks/guardian && chmod +x ~/.claude/hooks/guardian
```

## Configure

Add to your `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/guardian"
          }
        ]
      }
    ]
  }
}
```

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-12T00:00:00Z] BLOCKED | cwd=/home/user/project | reason=rm with force+recursive flags | command=rm -rf /
```

## Override

If a command is legitimately needed, run it **manually in your terminal** — the hook only intercepts Claude Code.

## Requirements

- Python 3.8+
- No pip dependencies
