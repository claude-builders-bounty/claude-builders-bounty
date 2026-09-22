# Destructive Bash command guard

Python 3.9+ standard-library `PreToolUse` hook for Claude Code. It returns exit
code 2 with a reason on stderr for matched destructive commands. Other commands
return 0 without an allow decision, preserving normal permission checks.

## Install (from this repository checkout)

```sh
python3 destructive-hook/install.py
```

Restart Claude Code and verify the Bash entry in `/hooks`. The installer copies
the guard to `~/.claude/hooks/destructive_guard.py`, merges a `PreToolUse` Bash
matcher into `~/.claude/settings.json`, and backs up existing settings once.
It never invokes a model or changes project files. Python's absolute executable
path is recorded; rerun installation if that interpreter moves. Intended for
Bash tool calls on macOS/Linux or a Bash-capable Windows Claude installation.
Installation is opt-in; tests use temporary homes and never modify real settings.

## Policy

- `rm` combining recursive and force flags, including split flags and long forms.
- `git push --force`, `-f`, force-with-lease, and force refspecs.
- SQL `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` lacking a top-level `WHERE`
  in the same statement. Comments, string literals and subqueries cannot supply
  that WHERE. Checks cover literal SQL arguments and common SQL-client pipelines.
- Literal nested `sh`/`bash`/`dash`/`zsh -c` commands and common wrapper prefixes.

Plain echo/printf/search examples are left alone unless sent to a SQL client.
Normal commands such as `git status`, `npm test`, ordinary `rm file`, and SQL
deletes with a WHERE clause keep their usual permission flow.

Blocked attempts append one JSON object per line to `~/.claude/hooks/blocked.log`
with UTC timestamp, full attempted command, project path (`cwd`), and reason.
Embedded newlines are escaped. A failed audit write still blocks and reports the
logging problem. The log is local and can contain sensitive command arguments;
do not upload it. New files use owner-only permissions where the OS supports them.

## Verification

```sh
python3 -m unittest discover -s destructive-hook -v
```

Tests feed JSON to the real hook process, assert its exit/stderr and audit record,
exercise benign and destructive examples, simulate log failure, and verify that
installation preserves other settings and is repeatable. Test commands are input
strings only: no destructive shell command or SQL statement is executed.

## Limits and removal

This is a best-effort accident guard, **not an authorization boundary** or full
Bash/SQL parser. Dynamically assembled commands, variable expansion, arbitrary
interpreter code, aliases, scripts/files containing SQL, dialect-specific SQL,
and deeply nested shell syntax can evade inspection or cause false positives.
A WHERE clause does not prove a delete is safe (for example `WHERE 1=1`). The
guard intentionally blocks force-with-lease as a stricter history policy.
Malformed hook input/quoting is blocked; a missing interpreter, disabled hook,
or hook timeout cannot provide protection. Keep normal permissions, backups,
database access controls, and human review.

To remove, delete only the matching Bash hook entry from settings.json, then
remove `~/.claude/hooks/destructive_guard.py`. Preserve other hooks and settings.

Protocol reference: [Claude Code hooks](https://code.claude.com/docs/en/hooks).
AI-assisted implementation; no live Claude session or paid model service was
used for validation. The subprocess tests exercise the documented hook protocol.
