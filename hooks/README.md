# Destructive Bash Command Blocker

Claude Code pre-tool-use hook that blocks dangerous bash commands before they run.

## Install

```bash
install -D -m 755 hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
```

Add it to your Claude Code settings:

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

## Behavior

The hook blocks:

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with a timestamp, attempted command, project path, and block reason.

Normal bash commands exit successfully and are not logged.

## Test

```bash
python3 tests/test_block_destructive_bash.py
```
