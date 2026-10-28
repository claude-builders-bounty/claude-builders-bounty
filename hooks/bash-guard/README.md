# Bash guard

A Claude Code `PreToolUse` hook for the `Bash` tool that blocks destructive
commands (bounty #3). Requires Python 3.9+. No packages, API keys or network
service are needed.

## Install

From this directory, one command:

```bash
python3 install_hook.py
```

This copies the hook to `~/.claude/hooks/bash_guard.py` and registers it in
`~/.claude/settings.json`, preserving unrelated settings and hooks. Restart
Claude Code afterward and check its `/hooks` menu. `CLAUDE_CONFIG_DIR` or
`--config-dir PATH` selects an alternate configuration directory. The hook
runs with the interpreter that ran the installer, so keep it installed.

## Policy

| Denied operation | Examples of recognized forms |
| --- | --- |
| Recursive forced removal | `rm -rf`, `rm -fr`, `rm -R -f`, `rm --recursive --force` |
| Forced push | `git push --force`, `-f`, `--force-with-lease`, `+main:main` refspecs |
| Drop table | Case-insensitive `DROP TABLE`, including comments between keywords |
| Truncate table | Case-insensitive `TRUNCATE [TABLE] name` |
| Unbounded delete | `DELETE FROM` without a `WHERE` belonging to that same statement |

The guard recognizes literal commands in command lists, common `sudo`, `doas`,
`env`, `command`, `nohup`, `time`, `nice`, `timeout` and `stdbuf` wrappers, the
command run by `find -exec/-execdir/-ok/-okdir` and `xargs`, literal shell `-c`
arguments, `eval`, substitutions and here-documents. `rm -- -rf` treats `-rf` as a filename. The Unix utility
`truncate -s 0 file` is separate from SQL truncation.

SQL is inspected in literal arguments/input to `psql`, `mysql`, `mariadb`,
`sqlite3`, `sqlcmd` and `duckdb`, including `--command=`, `--execute=`, here-docs,
here-strings and direct `echo`/`printf` pipes. Bare SQL examples are recognized
as well. SQL keywords are case-insensitive; shell executable names follow
their normal case-sensitive spelling.

Strings, quoted identifiers and ordinary SQL comments do not supply a WHERE
clause. A WHERE in another statement or a nested query does not qualify an
outer DELETE. A literal WHERE clause satisfies this policy; the hook does not
prove that its predicate is selective. MySQL executable comments require
manual review and are denied.

For example, `echo 'rm -rf example'`, `git status`, normal `git push`,
`psql -c 'DELETE FROM users WHERE id=7'`, and SQL string literals containing
destructive keywords are left to normal permission checks. A matching command
is denied even if it is in a branch that might not run or uses a dry-run flag.

## Decisions and audit log

The hook reads one JSON object from stdin. It never executes the command it
inspects. A denial returns `hookSpecificOutput` with `hookEventName` set to
`PreToolUse`, `permissionDecision` set to `deny`, and a specific
`permissionDecisionReason`. A safe command exits successfully without a
decision; the hook never grants an unconditional `allow`.

Each denial appends one UTF-8 JSON record to the installed hook's `blocked.log`:

```json
{"timestamp":"2026-10-24T17:00:00+00:00","command":"rm -rf 'example'","project_path":"/work/project","reason":"Blocked: rm combines recursive and force options."}
```

This is an illustrative record. Real records retain the original command,
including whitespace/newlines, and the supplied `cwd`. Writes are serialized
with an OS file lock. The log uses mode `0600` on POSIX; Windows permissions
depend on the containing directory's ACL. Command text may contain sensitive
arguments: keep the log private. No log data is uploaded or automatically
rotated.

Malformed input and inspection errors deny the request. Unknown command/path
fields are `null` when the input did not provide them. If the log cannot be
written, the command remains denied and the reason reports the logging error;
an unavailable filesystem cannot provide a persisted audit record.

Registration uses the long-standing single-string `command` form with a
10-second timeout and both the interpreter and script paths shell-quoted, so it
does not depend on newer hook fields. Failures inside the script itself are
fail-closed (a denial or exit code 2). The installer preserves other settings, refuses malformed settings or an
enabled `disableAllHooks`, and does not duplicate its registration on reinstall.

## Limits and verification

This is a literal-command policy, not a complete shell/SQL interpreter or a
sandbox. It does not resolve aliases, variables, generated/encoded commands,
arbitrary interpreter programs, sourced scripts, SQL loaded from files,
database stored routines or commands on remote hosts. It does not intercept
other tools such as PowerShell or Write. Keep Claude Code's own permissions
and filesystem/database protections in place. Unclosed quotes, incomplete
here-documents, executable SQL comments, requests over 1 MiB and nesting beyond
16 levels are denied for review rather than guessed safe.

Run the integration suite from this directory with
`python3 -B -m unittest discover -s tests -v`.
It installs into temporary directories under `.test-tmp`, reads the actual
registered command string and runs it through a shell with the event on stdin.
Every shell/SQL example is inert JSON input, never executed. Tests cover all
five rules, benign counterexamples, clause boundaries, Unicode and concurrent
logs, logging failure, malformed requests, installation paths and preservation
of unrelated configuration. POSIX modes and symlink refusal are checked on
Linux.

These are protocol/installation integration tests, not an authenticated Claude
Code session. They do not claim general shell-sandbox coverage or protection
from modifications to the hook/settings by another process with write access.
