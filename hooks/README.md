# Block Destructive Bash Commands

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

From this repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_commands.py ~/.claude/hooks/
python3 ~/.claude/hooks/block_destructive_commands.py --install
```

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON with a timestamp, attempted command, project path, and block reason.
