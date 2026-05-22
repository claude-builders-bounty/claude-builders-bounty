# Destructive Bash Blocker (Claude Code Hook)

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash/terminal commands.

## Features

- **Blocks dangerous commands** like `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` (without WHERE clause).
- **Silent pass-through** for all other safe commands.
- **Audit Logging**: Logs every blocked attempt with a timestamp, project path, and the blocked command to `~/.claude/hooks/blocked.log`.
- **Feedback**: Sends a clear stderr message to Claude explaining *why* the command was blocked.

## Installation

You can install this hook in 2 commands:

```bash
mkdir -p ~/.claude/hooks
curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/destructive-bash-blocker/pre-tool-use.py > ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## How it Works

When Claude Code attempts to run a bash tool, it pipes a JSON payload to the `pre-tool-use` script. The Python script parses the command, evaluates regex patterns for destructive actions, and if a match is found, writes to the audit log and exits with code `1`, printing an explanation to `stderr` which Claude can read.
