# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they can be executed.

## What It Blocks

| Pattern | Description |
|---------|-------------|
| `rm -rf` | Recursive force removal of files/directories |
| `DROP TABLE` | SQL table deletion |
| `TRUNCATE` | SQL table truncation (removes all data) |
| `DELETE FROM` without `WHERE` | SQL deletion without filtering |
| `git push --force` / `git push -f` | Force push that overwrites remote history |

## Features

- ✅ Blocks destructive commands with clear explanations
- ✅ Logs all blocked attempts to `~/.claude/hooks/blocked.log`
- ✅ Does not interfere with normal, safe bash commands
- ✅ Easy 2-command installation

## Installation

