# Claude Code Destructive Command Blocker

## Description

This is a Claude Code hook that blocks dangerous bash commands such as:

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a WHERE clause

## Installation

1. Make sure you have `jq` installed on your system
2. Copy `pre-tool-use-blocker.sh` to `~/.claude/hooks/pre-tool-use` and make it executable: `chmod +x pre-tool-use-blocker.sh`