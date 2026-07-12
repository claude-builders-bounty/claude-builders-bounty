# Block Destructive Bash Commands Hook

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they are executed.

## What it blocks

- `rm -rf` — recursive force delete
- `DROP TABLE` — SQL table deletion
- `git push --force` / `git push -f` — force push
- `TRUNCATE` — SQL table truncation
- `DELETE FROM` without a `WHERE` clause — unqualified SQL deletion

## Installation

