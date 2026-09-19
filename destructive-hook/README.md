# Destructive-command hook

A Python 3.9+ `PreToolUse` hook for the Bash tool. It never executes the inspected
command. It emits the documented `hookSpecificOutput.permissionDecision: deny`
response when a destructive pattern is found, with a reason visible to Claude.
For ordinary commands it exits silently, leaving normal permission checks intact.

## Install (two commands)

From a checkout of this contribution, in a terminal with Python 3.9+:

```sh
python -m unittest discover -s destructive-hook -p 'test_*.py'
python destructive-hook/install.py
```

Use `python3` if that is your interpreter name. The installer copies the script
to `~/.claude/hooks/destructive-guard.py`, adds a Bash-only PreToolUse entry to
`~/.claude/settings.json`, and preserves other settings/hooks. It stores a uniquely
named backup before changing existing settings and is idempotent. Invalid JSON
settings are rejected instead of replaced. Close other settings editors first.
The saved command uses your current Python executable, so reinstall after moving
that interpreter. Start a new Claude Code session after installation.

To uninstall, remove only the `PreToolUse` entry whose command points to
`destructive-guard.py`, then remove that script if desired. Keep other hooks and
settings. The log is retained for your review.

## Rules

| Pattern | Reason |
| --- | --- |
| `rm -rf`, `-fr`, `-r -f`, `-Rf`, `--recursive --force` | Recursive forced deletion bypasses ordinary prompts. |
| `git push --force`, `-f`, `--force-with-lease`, `+refspec` | Rewriting shared history requires separate review. |
| `DROP TABLE` | Table destruction should use a reviewed migration. |
| `TRUNCATE` | All rows are removed. |
| `DELETE FROM` without an outer `WHERE` | An unbounded delete can remove all rows. |

Command chains, common sudo/env wrappers, literal `bash -c`/`sh -c`, and `eval`
are inspected. SQL arguments to psql/mysql/mariadb/sqlite3/duckdb, piped SQL and
literal SQL statements are checked. SQL keywords in quoted strings or comments
do not count as a WHERE clause; neither does a WHERE inside a nested SELECT.
Normal commands such as `npm test`, `git status`, `git push`, `rm file.txt`, and
`psql -c "DELETE FROM users WHERE id=42"` continue through ordinary permissions.
Quoted documentation such as `echo 'rm -rf build'` is not treated as execution.

## Audit log

Each denial appends one JSON line to `~/.claude/hooks/blocked.log`, with a UTC
timestamp, exact attempted command, project path (`cwd` from the hook input),
and reason. New log files use owner-only permissions on POSIX. A log write error
is included in the denial message and never turns a block into permission.
Commands can contain secrets: treat this local log as sensitive and do not
upload it automatically. No telemetry or network calls are made.

## Verification and limits

The tests exercise real stdin/stdout hook invocations, the deny schema, log
appends, logging failures, silent normal commands and installation in temporary
homes. No destructive fixture is executed; command strings are only inspected.
Settings installation was tested in temporary homes, not applied globally.
The contract follows the [official hooks reference](https://code.claude.com/docs/en/hooks).
A signed-in interactive Claude Code session was unavailable during testing;
live UI interception is not claimed.

This is a guard against common mistakes, not a shell sandbox or complete Bash/SQL
parser. It does not resolve aliases, variables, generated/encoded commands,
external script/SQL-file contents, arbitrary interpreter APIs or all shell
grammar. A WHERE clause is a syntactic check, not proof that deletion is safe
(`WHERE 1=1` still matches every row). Keep normal permissions and backups.
Malformed shell quoting is denied with an explanation. Concurrent edits to
settings are unsupported; recheck settings after installation.
