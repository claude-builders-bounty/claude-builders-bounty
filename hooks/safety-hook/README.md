# Claude Code Safety Hook

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash and database commands before they are executed.

## Features
- Intercepts the `Bash` tool in Claude Code.
- Blocks destructive commands: `rm -rf`, `git push --force`, `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause.
- Logs every blocked attempt to `~/.claude/hooks/blocked.log` with a timestamp, project path, and the attempted command.
- Halts execution with a clear, descriptive error message.
- Allows all other normal commands to pass through safely.

## Installation

You can install this hook in your Claude Code environment with these two commands:

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/safety-hook/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use
```

## How It Works
When Claude Code attempts to run a bash command, it passes the tool name as an argument and the tool's JSON arguments via `stdin`. This script reads the JSON, extracts the `command` string, and uses Regex to pattern-match against known dangerous operations. If a match is found, it prints an error and exits with code `1`, causing Claude Code to abort the tool execution.
