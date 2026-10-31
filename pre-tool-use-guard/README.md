# PreToolUse guard: block destructive commands

A Claude Code `PreToolUse` hook that stops `rm -rf`, `git push --force`, `DROP TABLE`,
`TRUNCATE` and `DELETE FROM` without `WHERE` **before** they run, explains why, and logs
the attempt.

Written in Python 3 (standard library only). Works on macOS, Linux and Windows.

## Install

Two commands:

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pre-tool-use-guard/block-destructive.py -o ~/.claude/hooks/block-destructive.py
python3 ~/.claude/hooks/block-destructive.py --install
```

`--install` copies the script into `~/.claude/hooks/`, merges the hook into
`~/.claude/settings.json` (existing hooks and settings are preserved), and is
idempotent. Restart Claude Code afterwards.

Without curl — clone the repo and run:

```bash
python3 pre-tool-use-guard/block-destructive.py --install
```

Remove it again with `python3 ~/.claude/hooks/block-destructive.py --uninstall`.

## What gets blocked

| Rule | Matches | Example |
|---|---|---|
| `rm_rf` | any `rm` with a recursive flag (`-r`, `-R`, `--recursive`) **and** a force flag (`-f`, `--force`) | `rm -rf build/`, `sudo rm -fr /`, `rm -r -f ./out` |
| `git_push_force` | `git push` with `-f`, `--force`, `--force-with-lease`, `--force-if-includes`, or a `+refspec` | `git push --force origin main`, `git push origin +main` |
| `sql_drop_table` | `DROP TABLE` sent to a SQL client | `psql -c 'DROP TABLE users'` |
| `sql_drop_database` | `DROP DATABASE` / `DROP SCHEMA` | `mysql -e 'DROP DATABASE production'` |
| `sql_truncate` | `TRUNCATE [TABLE] …` | `psql -c 'TRUNCATE TABLE logs'` |
| `sql_delete_without_where` | `DELETE FROM …` with no `WHERE` in the same statement | `sqlite3 app.db 'DELETE FROM sessions'` |

The hook understands the shapes commands actually take:

- flags in any order or combined: `rm -rf`, `rm -fr`, `rm -Rf`, `rm -r -f`, `rm -rf --`;
- wrappers: `sudo`, `sudo -u root`, `env -i VAR=1`, `nohup`, `time`, `nice`, `xargs`, `command`;
- shell indirection: `bash -c 'rm -rf /'`, `sh -c "…"`, `eval '…'` (recursion depth capped at 4);
- command chains: `echo x && rm -rf out`, `cd /tmp; rm -rf /`, pipelines.

## What is deliberately allowed

The guard parses shell words instead of grepping the raw string, so destructive text in
*arguments* is not mistaken for execution:

```bash
echo 'rm -rf is dangerous'          # allowed
grep -rn 'DROP TABLE' migrations/   # allowed
git commit -m 'rm -rf cleanup'      # allowed
git log --grep 'push -f'            # allowed
npm run db:migrate                  # allowed (migrations are reviewed files)
psql -c 'DELETE FROM users WHERE id = 1'   # allowed
rm -f package-lock.json             # allowed (no recursive flag)
```

SQL is only inspected when the command actually invokes a SQL client (`psql`, `mysql`,
`mariadb`, `sqlite3`, `turso`, `libsql`, `duckdb`, `clickhouse-client`, `mongosh`, `mongo`),
so reading migrations or grepping for `DROP TABLE` never trips it.

## What Claude sees

Exit code `2` blocks the tool call and returns the reason as the tool result:

```
BLOCKED by pre-tool-use hook (rm_rf).
Command: rm -rf build/

Why: recursive + force delete is unrecoverable and almost always wider than intended:
a mistyped path, an unset variable or a missing slash turns `rm -rf $DIR/` into `rm -rf /`.

What to do instead: delete known files explicitly (`rm file1 file2`), or use `rm -r` without
`-f` so the shell asks before removing write-protected paths; for build artifacts prefer
the project's own clean task.
If the user explicitly approved this exact action, ask them to run it themselves, or set
CLAUDE_ALLOW_DESTRUCTIVE=1 for this session.
```

Every block is appended to `~/.claude/hooks/blocked.log` as JSON Lines:

```json
{"timestamp":"2026-10-31T04:12:03.481Z","decision":"blocked","rule":"git_push_force","command":"git push --force origin main","project":"/Users/dev/app","session_id":"abc123","tool":"Bash"}
```

The log rotates to `blocked.log.1` at 5 MB. Override the path with `CLAUDE_HOOK_LOG`.

## Bypass

When a destructive command is genuinely intended, the user runs it themselves or starts
Claude Code with:

```bash
CLAUDE_ALLOW_DESTRUCTIVE=1 claude
```

Bypassed commands are still logged (`"decision":"bypassed"`) and Claude sees a warning,
so the audit trail stays complete. The guard never silently permits a match.

## Design notes

- **Fails open.** A malformed hook payload, missing `tool_input.command`, or an unreadable
  log returns `0`. A guard that breaks the session on its own bug is worse than no guard.
- **No regex over the whole command line** for shell rules — `shlex` tokens, so quoting
  and argument text do not produce false positives.
- **Exit code 2, not JSON output** — supported by every Claude Code version that has hooks;
  stderr is surfaced to the model directly.
- **No external dependencies**, no network access, no writes outside `~/.claude/hooks/`.

## Test

```bash
cd pre-tool-use-guard && python3 -m unittest discover -s tests -v
```

13 tests: 28 blocking cases, 23 non-blocking cases, log format, bypass logging,
malformed payload handling, quote-aware splitting, recursion limit, and the `--check` CLI.

## Manual check

```bash
python3 block-destructive.py --check "rm -rf /"   # exit 2 + explanation
python3 block-destructive.py --check "ls -la"     # exit 0 + "allowed"
```

## Requirements

Python 3.8+. `--install` needs a Python interpreter on `PATH` for the hook command it writes
into `settings.json`; the absolute path of the interpreter that ran `--install` is used, so
a `py`/`python3`/`python` mismatch later does not break the hook.
