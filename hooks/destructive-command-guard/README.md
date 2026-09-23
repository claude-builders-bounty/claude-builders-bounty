# Destructive command guard

A small Python standard-library `PreToolUse` hook for Claude Code's **Bash** tool.
Prepared for [issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).
It inspects text; it never runs the submitted command.

## Install (one command after obtaining this folder)

Requires Python 3.9+ and a current Claude Code version supporting command hook `args`.
From this folder run:

```sh
python3 install.py
```

On Windows use `python install.py`. Restart Claude Code and inspect `/hooks` to
confirm the Bash PreToolUse handler loaded. The installer uses the same absolute
Python interpreter path that runs the installer, copies the guard into
`~/.claude/hooks/destructive_command_guard.py`, and adds its handler to
`~/.claude/settings.json`. Other settings and handlers remain present. It saves
the first pre-install settings as `settings.json.before-destructive-guard`.
Repeating installation with the same interpreter is idempotent. Existing guard
files with different contents are refused. Do not edit settings concurrently.
The backup is not an automatic rollback; remove only this handler to uninstall,
because restoring an old full backup could discard later settings changes.

## Covered commands

* `rm` with both recursive and force flags, including `-rf`, `-fr`, `-r -f`,
  `-Rf`, `--recursive --force`, common `sudo`/`env` prefixes and absolute paths.
* `git push --force`, `-f`, combined short flags, `--force-with-lease`,
  `--force-if-includes`, and `+` refspecs. Lease-protected pushes are deliberately
  denied too; this is a conservative policy, not a claim they equal plain force.
* Inline `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without a top-level `WHERE`
  in psql/mysql/mariadb/sqlite3/sqlcmd arguments and simple echo/printf pipelines
  into those clients. SQL comments and quoted strings cannot supply a WHERE.
* Shell separators, unquoted newlines and simple `sh`/`bash`/`zsh`/`dash -c`
  wrappers. Malformed quoting and excessive wrapper nesting are denied.

Normal commands return exit 0 with no output: this leaves Claude Code's normal
permission checks in control. A denial returns exit 0 and JSON containing
`hookSpecificOutput.permissionDecision: "deny"` plus a reason.
Malformed input is denied. Other tools are ignored. Each blocked Bash command
appends one JSON line containing UTC timestamp, exact command, cwd and reason
to `~/.claude/hooks/blocked.log`. Log write failure still denies the command and
adds the failure to the message. Logs can contain secrets present in commands;
protect the directory and manage retention. No network service or dependency is used.

## Limits

This is a best-effort accidental-deletion guard, **not a security boundary or a
complete Bash/SQL parser**. It does not resolve aliases/functions, environment
expansion, eval, encoded commands, arbitrary interpreters, scripts or SQL read
from files, command substitutions, heredocs, remote commands, or all wrapper
forms. Complex dialect-specific SQL (including nested CTE mutations), unusual
option forms and dynamically constructed commands can bypass the checks.
Text heuristics may deny harmless arguments that resemble commands. A WHERE
clause is only a syntactic exception: `WHERE true` can still delete every row.
Do not rely on this to contain untrusted code. Use least privilege, backups,
normal approval controls and a sandbox where warranted. This handler does not
cover Claude Code's separate PowerShell tool.

## Tests

```sh
python3 -B -m unittest -v test_guard.py
```

56 deterministic tests cover blocked/safe strings, newline and quoting cases,
SQL comment/string/subquery false-WHERE cases, JSON denial/no-decision protocol,
UTC audit content, logging failure, malformed input, unrelated tools, and
installer preservation/idempotency/invalid-settings refusal. Tests only inspect
command strings; none execute destructive commands. Installation tests use a
temporary directory. The subprocess protocol test sets both HOME and USERPROFILE
to a temporary directory. No installation into the real user home is performed.

Local verification: Python unit tests passed on Windows on 2026-09-23. A live
Claude Code session acceptance test has not been performed; installation alone
does not establish that the hook is active.

Protocol reference: [official Claude Code hooks documentation](https://code.claude.com/docs/en/hooks).
License: MIT, matching the upstream project; see LICENSE.
