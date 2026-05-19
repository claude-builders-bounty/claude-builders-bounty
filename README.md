# Claude Builders Bounty

## Destructive command pre-tool-use hook

Blocks risky bash commands before Claude Code runs them.

### Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use/block_destructive_commands.py ~/.claude/hooks/
```

### Configure Claude Code

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive_commands.py"
          }
        ]
      }
    ]
  }
}
```

The hook blocks:

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with timestamp, attempted command, project path, and reason.
