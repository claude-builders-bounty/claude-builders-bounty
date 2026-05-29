# Destructive Bash Command Hook

Claude Code `PreToolUse` hook that blocks risky Bash commands before execution.

## Install

```bash
python3 hooks/install_destructive_command_hook.py
```

The installer copies `block_destructive_bash.py` to `~/.claude/hooks/` and
registers it in `~/.claude/settings.json` for the `Bash` tool.

## Blocked Patterns

- `rm -rf`, including `rm -fr`, split flags, and long `--recursive --force`
- `DROP TABLE`
- `git push --force`, including `--force-with-lease` and `-f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked command is appended to `~/.claude/hooks/blocked.log` as JSON with
timestamp, attempted command, project path, and matched rule.

## Test

```bash
python3 -m unittest tests/test_block_destructive_bash.py
```
