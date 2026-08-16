# Block Destructive Commands Hook

This hook intercepts and blocks dangerous bash commands before they are executed. 

It blocks the following patterns:
- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with the timestamp, attempted command, project path, and the reason for blocking.

## Installation

Run the following commands to install the hook:

```bash
mkdir -p ~/.claude/hooks
cp block_destructive.py hooks.json ~/.claude/hooks/
```
