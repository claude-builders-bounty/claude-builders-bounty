# Block Destructive Bash Commands

Claude Code `PreToolUse` hook that denies dangerous Bash commands before they run.

## Installation

```bash
python3 install.py
```

The installer copies `block_destructive.py` to `~/.claude/hooks/` and adds a Bash `PreToolUse` hook to `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and `rm -fr`
- `rm -Rf`, `rm -fR`, and `rm --recursive --force`
- `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`, `DROP INDEX`, `DROP VIEW`, `DROP FUNCTION`, and `DROP PROCEDURE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- force-push bypasses such as `git push +main:main` and `git -c push.force=true push`
- `git reset --hard` and destructive `git clean` variants such as `git clean -fdx`
- destructive commands hidden behind shell wrappers such as `bash -c 'rm -rf build'`
- broad `find` deletes such as `find / -delete` or `find $HOME -delete`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause
- `UPDATE ... SET` statements without a `WHERE` clause
- `ALTER TABLE ... DROP`
- direct block-device writes/wipes such as `mkfs`, `mkswap`, `wipefs`, `dd ... of=/dev/sd*`, and redirects to `/dev/sd*`
- remote script execution through `curl|bash` or `wget|sh`
- shell fork bombs
- recursive permissive root-path permission changes such as `chmod -R 777 /...`

Read-only text inspection commands such as `grep`, `rg`, `cat`, `echo`, and `printf` are allowed to contain SQL-looking text unless the same command segment invokes a SQL client such as `psql`, `mysql`, or `sqlite3`.

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- timestamp
- attempted command
- project path
- block reason

## Hook Behavior

The hook reads Claude Code hook JSON from stdin. Non-Bash tool calls are allowed. Safe Bash commands return `continue: true`. Blocked commands return a `PreToolUse` `permissionDecision` of `deny` with a reason Claude can use to choose a safer command.
