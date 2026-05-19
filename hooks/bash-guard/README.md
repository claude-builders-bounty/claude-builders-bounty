# Claude Code Security Bash Guard

A `pre-tool-use` hook to prevent Claude from executing destructive bash or SQL commands.

## Features
Blocks:
- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`
- `DELETE FROM` (without `WHERE` clause)

Automatically logs attempts to `~/.claude/hooks/blocked.log` with timestamp, directory path, and attempted command.
Provides a clear message back to Claude explaining why the command was blocked.

## Installation

Run these two commands to install the hook:

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## Usage
Once installed, the hook runs automatically whenever Claude attempts to use a bash or shell tool. Dangerous commands will immediately fail and be logged.
