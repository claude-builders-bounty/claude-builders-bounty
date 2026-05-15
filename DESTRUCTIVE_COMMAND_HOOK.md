# Destructive Command Guard Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use/destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py && chmod +x ~/.claude/hooks/destructive_command_guard.py
```

```bash
python3 hooks/pre-tool-use/install_settings.py
```

The second command adds the hook to `~/.claude/settings.json` under a `PreToolUse` matcher for `Bash`.

## What It Blocks

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `TRUNCATE` / `TRUNCATE TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with timestamp, attempted command, project path, and matched pattern.

## Verify

```bash
python3 -m unittest discover -s tests
```
