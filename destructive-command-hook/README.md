# Destructive Command Guard Hook

Claude Code pre-tool-use hook that blocks dangerous bash commands before they run.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-hook/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

Then configure Claude Code to run `~/.claude/hooks/pre-tool-use.py` as a pre-tool-use hook.

## What it blocks

- `rm -rf` and close variants like `rm -fr`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked command is logged to `~/.claude/hooks/blocked.log` with timestamp, project path, and attempted command.
