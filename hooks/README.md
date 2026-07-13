# Pre-tool-use Safety Hook

Blocks destructive bash commands before Claude Code runs them:
`rm -rf`, `git push --force`, `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE`.

## Register (~/.claude/settings.json)
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [ { "type": "command", "command": "~/.claude/hooks/block_destructive.py" } ] }
    ]
  }
}
```
Every block is logged to ~/.claude/hooks/blocked.log.
