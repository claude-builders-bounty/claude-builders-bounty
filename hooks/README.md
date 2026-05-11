# Destructive Command Blocker

A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before they execute.

## Installation

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use ~/.claude/hooks/pre_tool_use && chmod +x ~/.claude/hooks/pre_tool_use
```

That's it. Claude Code detects hooks in `~/.claude/hooks/` automatically on next start.

## What It Blocks

| Pattern | Example | Why |
|---|---|---|
| Recursive force delete | `rm -rf /project/data` | Irreversible file deletion |
| Database destruction | `DROP TABLE users;` | Permanent data loss |
| Table truncation | `TRUNCATE TABLE logs;` | Non-recoverable row removal |
| DELETE without WHERE | `DELETE FROM users;` | Mass data deletion |
| Force push | `git push --force origin main` | Overwrites remote history |

Safe variants (with WHERE clause, normal `rm`, regular `git push`) pass through without interference.

## Logging

Every blocked command is recorded to `~/.claude/hooks/blocked.log` in JSONL format:

```json
{"timestamp": "2026-05-11T02:30:00Z", "command": "rm -rf /project", "reason": "...", "project": "/Users/me/my-project"}
```

## How It Works

The hook receives JSON on stdin with `tool_name` and `tool_input`. For Bash tool calls, it checks the command against compiled regex patterns. On match:

1. The command description is printed to stderr
2. Exit code 2 is returned (Claude Code protocol — blocks the tool call)
3. The attempt is logged to `blocked.log`

Non-matching commands and non-Bash tools pass through with exit code 0.
