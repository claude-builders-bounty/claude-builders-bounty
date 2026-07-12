# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they are executed.

## What It Blocks

- `rm -rf` and similar destructive remove commands
- `DROP TABLE` SQL statements
- `TRUNCATE` SQL statements
- `DELETE FROM` without a `WHERE` clause
- `git push --force` and `git push -f`

## Installation

