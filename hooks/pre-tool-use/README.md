# Destructive Bash Command Blocker

This Claude Code `PreToolUse` hook blocks destructive Bash commands before they run and logs each blocked attempt to `~/.claude/hooks/blocked.log`.

## Install in 2 Commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py
```

```bash
python3 ~/.claude/hooks/block_destructive_bash.py < hooks/pre-tool-use/examples/rm-rf.json
```

Add the hook to your Claude Code settings:

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

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Allowed commands return:

```json
{"continue": true}
```

Blocked commands return:

```json
{
  "continue": false,
  "decision": "block",
  "reason": "Blocked dangerous Bash command (...)"
}
```

Each blocked attempt is logged as JSON Lines with timestamp, attempted command, project path, and matched rule.
