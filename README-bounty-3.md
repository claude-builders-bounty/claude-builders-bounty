# Claude Code destructive-command guard

A dependency-free Python `PreToolUse` hook for Bash created for bounty #3.
It blocks the required destructive operations, logs every block, and stays
silent for normal Bash commands so Claude Code's normal permission flow remains
unchanged.

## What it blocks

- recursive + forced `rm`, including combined/separate flags, paths, shell
  chaining, command substitution, and `sudo`
- `DROP TABLE`
- `git push --force`, `--force-with-lease`, and `-f`
- `TRUNCATE`
- `DELETE FROM` without a real `WHERE` clause

For SQL, the guard recognizes raw destructive SQL and common database CLIs
(`psql`, `mysql`, `mariadb`, `sqlite3`, `duckdb`) while allowing harmless
text such as `echo 'DROP TABLE users'`. SQL comments or quoted text containing
the word `WHERE` do not bypass the `DELETE FROM` guard.

Every blocked attempt is appended to
`~/.claude/hooks/blocked.log` with an ISO-8601 UTC timestamp, project path,
and attempted command.

## Install — 1 command

Run this from this repository:

```bash
python3 install_hook.py
```

The installer copies the hook into `~/.claude/hooks/`, preserves unrelated
settings and existing hooks in `~/.claude/settings.json`, and registers the
script as a `PreToolUse` hook with matcher `Bash` using Claude Code's
command + args format. Running the installer again is idempotent.

Restart Claude Code after installation.

## Test

```bash
python3 -m unittest -v test_destructive_command_guard.py
```

The suite covers the required patterns, common shell bypass variants, harmless
commands, structured deny output, required log fields, and installer
idempotency/settings preservation.

## Hook behavior

Claude Code sends tool context as JSON on stdin. For a blocked Bash call, the
hook writes a structured response with:

- `hookEventName: "PreToolUse"`
- `permissionDecision: "deny"`
- a clear `permissionDecisionReason`

For a safe Bash command, non-Bash tool call, or malformed/non-actionable input,
the hook exits successfully without output.
