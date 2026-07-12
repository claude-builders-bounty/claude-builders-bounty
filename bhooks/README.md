# Claude Code Pre-Tool-Use Hook: Block Destructive Commands

A security hook for [Claude Code](https://docs.anthropic.com/claude-code) that intercepts and blocks dangerous bash commands before they execute.

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` | Irreversible recursive deletion |
| `DROP TABLE` | Destructive SQL — table removal |
| `git push --force` | Overwrites remote history |
| `TRUNCATE` | Wipes all table data |
| `DELETE FROM` without `WHERE` | Deletes all rows unintentionally |

## Installation

