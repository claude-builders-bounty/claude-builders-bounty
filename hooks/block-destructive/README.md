# Destructive Bash Blocker Hook

This implements bounty #3 as a Claude Code `PreToolUse` hook for the `Bash` tool. The hook reads Claude Code's JSON hook payload from stdin and exits with code `2` when a destructive command should be blocked, which prevents the tool call and sends the stderr message back to Claude.

## Install

```bash
python hooks/block-destructive/install.py
claude
```

The installer copies the hook to `~/.claude/hooks/block-destructive.py` and updates `~/.claude/settings.json` with a `PreToolUse` matcher for `Bash`.

## Blocked Patterns

- `rm -rf` and equivalent combined flags such as `rm -fr`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, project path, and reason.

## Verification

```bash
python -m unittest discover -s tests
```

Normal commands return exit code `0`, produce no stderr, and do not write to the blocked log.
