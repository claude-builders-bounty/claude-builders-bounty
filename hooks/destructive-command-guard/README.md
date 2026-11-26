# Destructive command guard

A Python 3.9+ standard-library-only `PreToolUse` hook for Claude Code's `Bash`
tool. It inspects command text without executing it. This implements bounty
[#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3).

## Install

Requires Python 3.9+ and a current Claude Code version supporting command hooks
with an `args` array (see the [official hooks reference](https://code.claude.com/docs/en/hooks)).
From a checkout of this contribution, installation is one command:

```sh
python3 hooks/destructive-command-guard/install.py
```

For a fresh checkout of the submitted branch, these are the complete two commands:

```sh
git clone --branch bounty-3-destructive-command-guard https://github.com/adria113/claude-builders-bounty.git command-guard
python3 command-guard/hooks/destructive-command-guard/install.py
```

The installer copies `guard.py` to `~/.claude/hooks/destructive_command_guard.py`
and registers it in `~/.claude/settings.json` for `PreToolUse`, matcher `Bash`.
It uses an absolute Python executable plus an argument array, so paths containing
spaces or shell metacharacters do not need shell quoting. Start a new Claude Code
session after installation so that it loads the updated configuration.

Existing settings and other hooks are preserved. Before changing an existing
settings file, the installer saves its exact bytes to `settings.json.bak` (or
the next unused `.bak.N` name). Reinstalling updates the script without duplicating
the hook. Invalid configuration is reported rather than overwritten. The optional
`--claude-dir PATH` installs to a separate configuration directory for testing;
the guard's audit path remains the bounty-specified `~/.claude/hooks/blocked.log`.

## What it checks

| Command | Decision |
| --- | --- |
| `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force` | Block |
| `git push --force`, `git push -f` | Block |
| `git push --force-with-lease`, `git push origin +main` | Block too: they can replace remote history |
| `DROP TABLE`, `TRUNCATE [TABLE]` | Block |
| `DELETE FROM` without a `WHERE` in that deletion's own scope | Block |
| `rm report.tmp`, `git push origin main`, `DELETE FROM users WHERE id=42` | Leave to Claude Code's normal permissions |
| `echo 'rm -rf /tmp/example'`, `printf '%s\n' 'DROP TABLE users'` | Allow: these only print text |

Detection handles common absolute command paths, assignments, `sudo`/`env`/
`command` wrappers, command chains, substitutions, `sh`/`bash` `-c` invocations,
and literal here-documents/here-strings. SQL is inspected in direct statements,
common `psql`/`pgcli` `-c`, `mysql`/`mariadb` `-e`, `sqlite3`/`duckdb` positional
queries, and input piped or redirected as literal text to those clients.
Literal `echo`, `printf` (`%s`/`%%`), and here-document `cat` pipelines can feed
a recognized shell or SQL client. SQL comments and quoted values do not count as
a `WHERE` clause. Each deletion in a multi-statement query is checked separately;
a subquery's `WHERE` does not protect an unconditional outer deletion.

## Hook behavior and audit log

Input is Claude Code's JSON event on standard input. For example, this is test
data for the hook, **not a shell command to execute**:

```json
{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/work/project","tool_input":{"command":"rm -rf ./example"}}
```

- Blocked: exit **2**, with a short explanation on stderr for Claude Code.
- Allowed or unrelated event/tool: exit **0**, with no stdout or stderr. The hook
  does **not** issue an explicit permission grant or bypass other permission rules.
- Invalid Bash input or a detected parsing error: block with a diagnostic.
- Failure to write the audit log: report that failure and **still exit 2**.

Each denial appends one JSON line to `~/.claude/hooks/blocked.log` containing
`timestamp` (UTC), the original `command`, `project_path` (event `cwd`), and
`reason`. JSON encoding preserves multiline commands without forging extra log
records. New logs are created with owner-only permissions; non-regular log files
and symlinks are rejected where the operating system supports that check.
The log is local and contains full attempted commands, which may include secrets:
do not publish it without review. The hook does not read transcripts or use the
network.

## Boundaries

This is a pattern guard against common mistakes, **not a security sandbox or a
complete Bash/SQL interpreter**. It does not resolve shell aliases/functions,
variable-generated command names/options, executable files, SQL files, remote
commands, arbitrary programming-language code, encoded payloads, or every dialect
and wrapper option. It cannot prevent another tool or a user from editing or
disabling the hook. Complex shell syntax can be conservatively rejected.

`WHERE 1=1` still satisfies the requested syntactic `WHERE` check; this does not
prove that a deletion is safe. SQL text fed through an unknown producer or shell
formatter is outside the literal-input checks. Keep Claude Code permissions,
database access controls, backups, and human review in place.

## Verify without executing dangerous commands

From the repository root:

```sh
python3 -m unittest discover -s hooks/destructive-command-guard/tests -v
```

The tests pass dangerous strings to the inspection function or to the hook's
JSON stdin. They never execute those strings. Integration and installation tests
use temporary homes/configuration directories and leave your real settings alone.

## Uninstall

Remove only the `PreToolUse` handler whose `args` points to
`destructive_command_guard.py`, keeping other handlers and settings. Then remove
that script. Retain or delete `blocked.log` according to your own needs. An old
settings backup should only be restored if you have checked that doing so would
not discard changes made since installation.
