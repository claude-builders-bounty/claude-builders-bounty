# Safe Bash Hook for Claude Code

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash/SQL commands before they execute.

## Features
- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` (without `WHERE`).
- Only intercepts the `Bash` tool; leaves everything else alone.
- Logs all blocked attempts locally to `~/.claude/hooks/blocked.log` with timestamps and paths.

## Installation

Run these two commands in your terminal:

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## How it works
When Claude attempts to use a tool, it pipes the payload to standard input. This script parses the JSON, checks if the tool is `Bash`, and runs a regex match against the destructive patterns. If a match is found, it returns `{"status": "rejected"}` and a clear message back to Claude explaining why it was blocked.
