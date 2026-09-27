# Destructive command guard

A Python 3.10+ standard-library PreToolUse hook for Claude Code's Bash tool. It
blocks recursive force deletion, forced Git pushes, DROP TABLE, TRUNCATE,
and DELETE FROM statements without a real top-level WHERE clause. It inspects
simple shell sequences, command substitutions, process substitutions, wrappers,
here-strings to shell and SQL clients, and common here-doc input without
executing the submitted command.

## Install

From this folder, run one command:

    python3 install.py

On Windows, use python install.py. Review ~/.claude/settings.json and restart
Claude Code; the hook is registered for Bash PreToolUse calls. The installer
copies the script and adds one handler while preserving existing settings. It
is idempotent and refuses to replace a different guard file or malformed
settings. To uninstall, remove only this handler and the copied script; do not
restore an old whole-file backup over newer settings.

The hook uses the current Claude Code hookSpecificOutput.permissionDecision
format. Safe or unrelated tool calls return no decision, so normal permission
handling remains in control.

## What it checks

- rm when recursive and force flags are combined, in either order, including
  separated flags, long flags, absolute paths, sudo/env prefixes, and the
  -- option terminator.
- git push with --force, -f, force-with-lease variants, force-if-includes,
  or a + refspec (including after --); common git -C and git -c prefixes are handled.
- SQL sent with common psql, mysql, mariadb, sqlite3, and sqlcmd command
  options, simple producer-to-client pipes, a SQL here-doc, or a here-string.
- DROP TABLE, TRUNCATE, and a DELETE FROM lacking a top-level WHERE.
  Comments and quoted values do not count as a WHERE.
- bash/sh/zsh/dash -c, eval, $() and backtick command substitutions, process
  substitutions, common launchers such as sudo/env/timeout/xargs, and commands
  passed through find's -exec/-execdir/-ok actions. The env split-string option
  accepts separate, --split-string=value, and attached -Svalue forms. Quoted
  examples and shell comments are left alone; command-like text passed to echo is not treated as
  an executed command.

Every blocked event appends a JSON line to ~/.claude/hooks/blocked.log with
the UTC timestamp, full attempted command, and project_path provided by the
hook event. The message sent back to Claude explains the block. If logging
fails, the command is still denied and Claude is told about the logging error.
The log can contain secrets present in commands; protect it and manage its
retention.

## Tests

    python3 -B -m unittest -v

The tests exercise the hook protocol and command text only. They do not execute
destructive operations or install anything into the current user's home.

## Limits

This is a best-effort accidental-operation guard, not a security boundary or a
complete Bash/SQL parser. It does not resolve aliases, shell functions,
environment-variable-generated command names, commands read from external
scripts/SQL files, arbitrary interpreters, or every dialect-specific SQL
construct. A syntactic WHERE such as WHERE TRUE is allowed and can still match
every row. Keep normal permission controls, backups, and least-privilege access
in place. The hook does not cover PowerShell.

Protocol reference: https://code.claude.com/docs/en/hooks
