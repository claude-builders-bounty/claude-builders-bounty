# Claude Code Destructive Command Blocker

Pre-tool-use hook that blocks dangerous Bash commands before Claude Code runs them.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use-blocker/block_destructive.py ~/.claude/hooks/block_destructive.py
python3 ~/.claude/hooks/block_destructive.py < hook-payload.json
```

Add the copied script to your Claude Code `pre-tool-use` hook config for Bash tool calls.

## Blocked patterns

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- timestamp
- attempted command
- project path
- block reason

Normal Bash commands exit with status `0`. Blocked commands exit with status `2` and print a clear explanation for Claude.
