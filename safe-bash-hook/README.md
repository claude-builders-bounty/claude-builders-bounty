# Claude Code Pre-Tool-Use Hook: Safe Bash

This hook intercepts destructive `Bash` commands executed by Claude Code (like `rm -rf`, `DROP TABLE`, `git push --force`) to protect your system and data.

## Features
- Blocks `rm -rf`
- Blocks `DROP TABLE`
- Blocks `TRUNCATE`
- Blocks `git push --force`
- Blocks `DELETE FROM` without a `WHERE` clause
- Logs all blocked commands to `~/.claude/hooks/blocked.log`

## Installation

Run these two commands to install and register the hook globally in Claude Code:

```bash
mkdir -p ~/.claude/hooks && curl -sL https://raw.githubusercontent.com/claudebounty/claude-builders-bounty/main/safe-bash-hook/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py && ~/.claude/hooks/pre-tool-use.py --install
```

*(If you are submitting this via a fork, you can manually point the URL to your fork, or just copy the file directly to `~/.claude/hooks/` and run it with `--install`).*

## How it works

The hook uses the official `pre-tool-use` lifecycle event in Claude Code. Every time Claude attempts to run a bash command, the JSON data of the tool call is passed to this script. If a destructive pattern is detected, the script prints an error to `stderr`, exits with code `2`, and logs the attempt.

**Log Format (`~/.claude/hooks/blocked.log`)**:
```
[2026-03-29T10:00:00.000] BLOCKED: rm -rf node_modules | PROJECT: /Users/dev/project | REASON: rm -rf (destructive deletion)
```