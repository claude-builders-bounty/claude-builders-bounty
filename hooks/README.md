# Destructive Bash command hook

A dependency-free Python 3.10+ `PreToolUse` hook for Claude Code. It reads the
JSON event on stdin and inspects `tool_input.command`; it never runs that command.
It blocks with exit code **2** and a reason on stderr. An ordinary command exits
0 without an `allow` decision, preserving Claude Code's normal permission checks.
The protocol follows the [official hooks reference](https://code.claude.com/docs/en/hooks).

## Install in two commands

From a Bash terminal with Python 3 installed:

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git claude-builder-hooks
python3 claude-builder-hooks/hooks/install.py
```

Until this contribution is merged, clone the PR branch instead of the default
branch. If you already have this checkout, only the second command is needed.
On Windows, use `python` if that is your Python executable name. The installer
registers the exact interpreter used to run it, so do not remove that interpreter.

The installer copies the hook to `~/.claude/hooks/block_destructive.py` and merges
a `Bash` matcher into `~/.claude/settings.json`. It preserves unrelated settings
and hooks, creates an exact backup at `settings.json.before-destructive-hook`,
and is idempotent. Invalid JSON or a different existing script at the destination
stops installation rather than overwriting it. Start a new Claude Code session
and inspect `/hooks` to verify registration. The integration targets the **Bash**
tool; PowerShell-specific commands are outside this hook's scope.

## Blocked patterns

| Command | Reason |
| --- | --- |
| `rm -rf sample`, `rm -fr sample`, `rm -r -f sample` | Recursive forced deletion |
| `git push --force`, `git push -f` | Forced remote history update |
| `DROP TABLE customers` | Table removal |
| `TRUNCATE customers` | Removal of all rows |
| `DELETE FROM customers` without a real `WHERE` | Unrestricted deletion |

Long rm options, common wrappers such as `sudo`/`env`, command chains, literal
`sh`/`bash -c` scripts and command substitutions are inspected. Forced git
refspecs and `--force-with-lease` are also blocked. SQL is inspected in plain
statements, mysql/mariadb `-e`/`--execute`, psql `-c`/`--command`, sqlite3 query
arguments, simple echo/printf pipelines to those clients, and literal heredocs.
Each SQL statement is checked independently. A `WHERE` in a string, comment or
nested query does not qualify as the DELETE statement's WHERE clause.

`echo 'rm -rf sample'`, `grep 'DROP TABLE' fixture.sql`, a normal git push,
`rm -f sample.txt`, and `DELETE FROM customers WHERE id=1` remain unchanged.
This is a literal-command guard, not a shell/SQL sandbox: aliases, variables,
encoded or dynamically generated scripts, commands loaded from files, unusual
client/dialect syntax and arbitrary interpreter programs can escape static
inspection. Keep normal Claude permissions and least-privilege credentials.
The hook does not claim that a WHERE clause makes a deletion safe. Incomplete
shell quoting, invalid event input and excessive nesting block with an explicit
inspection error.

## Audit log

Blocked commands append one JSON record per line to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-10-05T18:00:00+00:00","command":"rm -rf sample","project_path":"/project","reason":"rm with recursive and force options deletes trees without prompting"}
```

The timestamp is UTC; the project path comes from the hook event's `cwd`. JSON
escaping keeps multiline commands in a single record. On POSIX the new log is
created with mode 0600. Commands can contain sensitive values: keep this local
log private and manage retention. If logging fails, the command remains blocked
and stderr reports the audit failure.

## Verification

```bash
python3 -m unittest discover -s hooks -p test_hook.py -v
```

The tests cover blocked patterns and ordinary commands, the stdin/exit/stderr
contract, append-only audit records, malformed input, a failed audit destination,
and settings merge/idempotence/backup preservation. All command examples are
strings passed to the hook; no rm, git push or database command is executed.
Tests use temporary homes. The integration was verified with synthetic hook
events on Windows; no live Claude Code session or POSIX runtime is claimed.

To uninstall, remove this hook's Bash entry from `settings.json` and its script.
Keep the audit log if desired. Restore the backup only after checking for settings
changes made since installation.
