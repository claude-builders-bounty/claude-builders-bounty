# Claude Code Security Hook

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash commands before they are executed. 

## Features
Blocks the following commands automatically:
- `rm -rf` (and variations like `rm -fr`, `rm -r -f`)
- `DROP TABLE`
- `git push --force` (and `git push -f`)
- `TRUNCATE`
- `DELETE FROM` (if it lacks a `WHERE` clause)

It will block the execution, return a clear rejection message to Claude, and log the attempt locally to `~/.claude/hooks/blocked.log`.

## Installation (2 Commands)

Run these two commands in your terminal to install the hook globally for Claude Code:

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use
```

## Logs
Whenever Claude tries to run a blocked command, it gets appended to `~/.claude/hooks/blocked.log` with the timestamp and project path.
