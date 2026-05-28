# Claude Builders Bounty — Safe Bash Hook

A Claude Code `pre-tool-use` hook that blocks destructive Bash commands before execution.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_safe_bash.py ~/.claude/hooks/pre_tool_use_safe_bash.py
chmod +x ~/.claude/hooks/pre_tool_use_safe_bash.py
```

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` / `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Log format includes timestamp, matched rule, project path, attempted command.

## Behavior

Normal bash commands exit `0` and continue. Dangerous commands exit `2`, print a clear message to Claude, and are logged.
