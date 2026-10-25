# Destructive-command guard

A Python standard-library `PreToolUse` hook for Claude Code's Bash tool.

## Install

Requires Python 3.8+ and Git. Run these two commands:

```sh
git clone https://github.com/soundcake/claude-hook-bounty-20261025.git --branch bounty/3-destructive-command-hook
python3 claude-hook-bounty-20261025/hooks/install.py
```

Start a new Claude Code session after installation. The installer copies the hook
to `~/.claude/hooks/destructive_guard.py` and adds its Bash `PreToolUse` entry to
`~/.claude/settings.json`. It preserves existing settings and hooks, backs up a
changed settings file, and does not duplicate the entry when run again with the
same Python interpreter. Invalid settings are left untouched.

## Behavior

The hook reads the tool event as JSON on stdin. A denied command produces a
`hookSpecificOutput` with `permissionDecision: "deny"` and a specific explanation.
Ordinary commands exit successfully without output, leaving Claude Code's normal
permission checks in place. See the [official hook protocol](https://code.claude.com/docs/en/hooks#pretooluse-decision-control).

| Command | Result |
| --- | --- |
| `rm -rf directory` (including split flags, `-fr`, `-R`, and long flags) | Denied |
| `git push --force` (including `-f`, force-with-lease, and `+` refspecs) | Denied |
| `DROP TABLE users` | Denied |
| `TRUNCATE TABLE users` | Denied |
| `DELETE FROM users` | Denied |
| `DELETE FROM users WHERE id = 42` | Normal permission flow |
| `git push origin main`, `rm file.txt`, `npm test` | Normal permission flow |
| `echo 'rm -rf example'` | Normal permission flow |

Literal shell commands are checked across command lists, common `sudo`/`env`/
`command` wrappers, shell `-c` arguments, `eval`, and command substitutions.
SQL is inspected in `psql`, `mysql`, `mariadb`, `sqlite3`, `duckdb`, and `sqlcmd`
arguments, literal `echo`/`printf` input, and here-documents. Each SQL statement is
checked separately; strings, comments and quoted identifiers do not count as a
`WHERE` clause. A `WHERE` inside a nested query does not qualify the outer DELETE.
The hook inspects text in the Bash tool call; it does not read scripts/SQL files,
resolve aliases, expand variables, or evaluate generated commands.

Every denied command appends a JSON line to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-10-25T08:00:00+00:00","command":"rm -rf example","project_path":"/work/project","reason":"rm with recursive and force flags can delete a directory tree without confirmation."}
```

The project path comes from the event's `cwd`. The log is created with mode `0600`.
If logging fails, the command remains denied and the explanation includes the log
error. Malformed Bash events and unclosed shell quotes are denied with an input
error. Other tools and events are ignored.

## Test

From the repository root:

```sh
python3 -m unittest discover -s hooks -v
```

Tests inspect command strings without executing them. They cover blocked/ordinary
commands, quoting, SQL statement boundaries, JSON output, append-only log records,
log failures, and installation into a temporary home with existing settings.

## Remove

Remove the Bash handler whose command points to `destructive_guard.py` from
`~/.claude/settings.json`, then delete that script. Keep any other hook entries.
Start a new Claude Code session. The log and settings backups remain available.
