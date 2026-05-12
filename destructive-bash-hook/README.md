# Destructive Bash PreToolUse Hook

Blocks dangerous Claude Code Bash tool calls before they run.

## Install

```sh
mkdir -p ~/.claude/hooks && cp destructive-bash-hook/block_destructive_bash.py ~/.claude/hooks/
```

```sh
chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Add the `PreToolUse` entry from `settings.example.json` to your Claude Code settings.

## What it blocks

- `rm -rf` and equivalent combined short options such as `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause
- `git push --force` and `git push -f`

Every blocked command is appended to `~/.claude/hooks/blocked.log` with:

- UTC timestamp
- project path
- block reason
- attempted command

The hook exits with code `2` when it blocks a command, which prevents the Bash tool call and sends the reason back to Claude Code on stderr.

Normal Bash commands exit with code `0` and continue without output.
