# Opt-in destructive-command hook for Claude Code

Implements bounty #3's named command patterns. This package is for a user who
chooses to install this restriction; it is not installed by running its tests.
It does not alter a tool bridge, another agent's policy or existing credentials.

## Install (one command from this directory)

```sh
python3 install.py
```

This writes `~/.claude/hooks/destructive-command-guard.py` and merges one Bash
PreToolUse entry into `~/.claude/settings.json`. It preserves all other settings
and avoids duplicate registration. `--config-dir PATH` installs into an explicit
alternate configuration for testing. Existing conflicting hook code or malformed
settings are not silently replaced. Start a new Claude Code session afterward.

## Behavior

The hook reads Claude's JSON from stdin. Bash commands containing recursive plus
forced rm, unconditional force pushes (including +refspec), DROP TABLE, TRUNCATE,
or DELETE FROM without an outer WHERE predicate receive a documented PreToolUse
JSON `deny` decision and a specific explanation. Split/long rm flags and common
sudo, env, shell -c, find and xargs forms are covered. `--force-with-lease` is not
unconditional force and is not blocked by this rule. Git's normal push and safe
rm variants remain unchanged.

SQL inspection handles direct SQL strings and common psql/sqlite3/mysql/mariadb/
sqlcmd/duckdb calls. It ignores SQL string literals and comments before matching
keywords and checks WHERE within each statement, so a later statement, a comment
or a nested SELECT cannot supply the missing DELETE predicate.

Normal commands and non-Bash tools emit `{}` and exit 0, leaving Claude's existing
permission decisions in charge. This hook never returns an allow override and
never executes the attempted command itself.

Each blocked attempt appends one JSON line to `~/.claude/hooks/blocked.log` with
UTC timestamp, attempted command, project path and reasons. The log is created
owner-only (0600), so other local users cannot read command contents by default.
Commands can contain secrets: treat this log as private and do not publish it.
If logging fails, the attempted operation remains denied and the failure is
explicit. No log is written for unblocked commands.

## Scope and limits

This is a static pattern hook, not a security boundary against an adversarial
programmer. It does not interpret arbitrary variable expansion, aliases,
functions, encoded scripts, SQL loaded from external files or arbitrary language
APIs. Shell command substitutions and complex heredocs are not fully parsed;
use OS isolation and database permissions for a real execution boundary. It
cannot prove that a permitted command is non-destructive. Conversely, malformed
shell quoting produces a refusal with an explanation rather than an invented
parse. These limitations are deliberate and testable, not hidden guarantees.

## Verify without installing or executing destructive commands

```sh
python3 -B -m unittest discover -s tests -v
```

The tests pass command strings as input data, inspect the returned decision and
read a temporary log. Installation tests point only into temporary directories.
No attempted destructive shell command or SQL statement is executed.

Format reference: https://code.claude.com/docs/en/hooks-guide#structured-json-output
