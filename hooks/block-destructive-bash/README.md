# Block Destructive Bash Commands

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-bash/block_destructive_bash.py ~/.claude/hooks/
python3 ~/.claude/hooks/block_destructive_bash.py --install
```

The installer writes this matcher to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked Patterns

- `rm -rf`, including reordered flags such as `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `DELETE FROM ...` statements that do not include a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with the timestamp, project path, and attempted command.

Claude Code blocks `PreToolUse` hooks when the hook exits with code `2`; the script writes a concise explanation to stderr so Claude can choose a safer alternative.
