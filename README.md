# Claude Builders Bounty

Hook package for bounty issue #3.

## What it does

This repo ships a Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run:

- `rm -rf`
- `git push --force`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without `WHERE`

Blocked attempts are written to `~/.claude/hooks/blocked.log` with a timestamp, the attempted command, and the project path.

## Install

```bash
mkdir -p ~/.claude/hooks ~/.claude && cp .claude/settings.json ~/.claude/settings.json && cp hooks/block_destructive_bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_bash.py
python -m unittest discover -s tests
```

The first command installs the hook and settings. The second command runs the tests.

## Files

- `hooks/block_destructive_bash.py` - hook entrypoint
- `.claude/settings.json` - Claude Code hook registration
- `tests/test_block_destructive_bash.py` - matcher and runtime tests

## License

MIT
