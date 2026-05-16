# Destructive Bash Guard Hook

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install

Run these two commands from the repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-bash-guard/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 ~/.claude/hooks/block_destructive_bash.py --install
```

The installer adds a `PreToolUse` matcher for `Bash` in `~/.claude/settings.json`.

## Blocks

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line is JSON with:

- `timestamp`
- `attempted_command`
- `project_path`
- `reason`

## Behavior

Normal Bash commands exit successfully and produce no output. Blocked commands exit with code `2`, which Claude Code treats as a blocking `PreToolUse` error and feeds back to Claude.

