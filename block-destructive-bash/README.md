# block-destructive — a Claude Code hook that stops destructive Bash commands

A `PreToolUse` hook for Claude Code that inspects every Bash tool call before
it runs and **blocks the commands that permanently delete data or rewrite
shared history**: recursive force-deletes, force pushes, and destructive SQL.
Every blocked attempt is appended to an audit log, and Claude gets a clear
message explaining what was blocked and why, so it can adjust instead of
retrying blindly.

Normal commands are never touched: the hook parses the command with a real
shell tokenizer, so `echo "rm -rf is dangerous"` and `rm -f file.txt` pass
through silently while `sudo rm -rf /`, `git push -f`, and
`mysql -e "DELETE FROM users"` are stopped. Pure Python 3 stdlib — no
dependencies, no network, sub-millisecond per call.

## Install (2 commands)

```bash
git clone <this-repo-url> && cd hook-block-destructive
./install.sh
```

`install.sh` copies `block_destructive.py` to `~/.claude/hooks/` (mode 0755)
and merges the wiring into `~/.claude/settings.json` — idempotently, backing
the old file up to `settings.json.bak` first. Then restart Claude Code (or
open a new session) and the hook is live.

Prefer to wire it by hand? Copy the script yourself and add
[`settings.snippet.json`](settings.snippet.json) to `~/.claude/settings.json`,
replacing `/home/YOUR_USER` with your home directory.

## What gets blocked

| Rule | Examples |
| --- | --- |
| `rm` recursive **and** forced, any spelling | `rm -rf x`, `rm -fr x`, `rm -r -f x`, `rm --recursive --force x`, bare `rm -rf` |
| `rm --no-preserve-root` | `rm --no-preserve-root -rf /` |
| Recursive `rm` of a catastrophic target, even without `-f` | `rm -r /`, `rm -r ~`, `rm -r $HOME`, `rm -r ..` |
| Forced `rm` of `/` or home, even without `-r` | `rm -f /` |
| Force push, every spelling | `git push -f`, `--force`, `--force-with-lease`, `--force-if-includes`, `git push origin +main` |
| Destructive SQL run through a real client (`mysql`, `mariadb`, `psql`, `sqlite3`, `duckdb`, `mysqlsh`, `sqlcmd`, `clickhouse-client`, `cqlsh`) or pasted raw into the shell | `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`, `TRUNCATE [TABLE]`, `DELETE FROM …` with **no WHERE clause** |

Detection sees through the usual disguises: leading wrappers (`sudo`, `env`,
`VAR=1`, `xargs`), chained commands (`&&`, `;`, `|`), paths (`/bin/rm`),
`git -C <dir> push`, SQL piped or heredoc'd into a client, and several
statements in one string (each `DELETE FROM` needs its own WHERE).

## What is deliberately allowed

* `rm -f file.txt`, `rm file.txt`, `rm -r build/` — ordinary targeted deletes.
  (A recursive delete of one named directory is a daily operation; adding
  `-f`, or aiming at `/`, `~`, `$HOME`, `.`/`..`, is what crosses the line.)
* `git push origin main`, `git push -u origin feature/x`, `--tags`, `--dry-run`.
* `DELETE FROM t WHERE id=1` — a targeted delete with a WHERE clause.
* Merely *mentioning* dangerous text: `echo "rm -rf is dangerous"`,
  `grep -rn "DROP TABLE" .`, `cat rm-guide.md`. Quoted strings are tokens, not
  commands, and SQL checks only run when a database client is actually
  executing (or SQL was pasted as the command itself).
* The shell utility `truncate -s 0 app.log` — not the SQL statement.

## Logging

Every block appends one line to **`~/.claude/hooks/blocked.log`**:

```
[2026-10-08T23:56:11+00:00] cwd=/tmp/fakehome-test/proj rule="git force push (--force)" command=git push --force origin main
```

Timestamp (ISO 8601 with timezone), the project path (`cwd` from the hook
payload), the rule that fired, and the attempted command (newlines escaped so
it stays one line). If the log can't be written, the command is still blocked.

## When something is blocked

The hook answers with the documented `PreToolUse` deny decision and a reason
Claude can read, e.g.:

> Blocked by the block-destructive hook: this command matches the
> 'git force push (--force)' rule and was NOT executed. … If the operation is
> genuinely intended, run it manually in a terminal outside Claude Code. To
> make it pass, narrow it instead: remove -r/-f from rm, drop --force from
> git push, or add a WHERE clause to the DELETE.

Safe commands get literally nothing: exit 0 and empty stdout.

## Tests

```bash
python3 tests/run_tests.py
```

* `tests/corpus_dangerous.txt` — 34 dangerous commands, all must block.
* `tests/corpus_safe.txt` — 25 safe near-misses, all must pass untouched.
* Plus robustness checks (malformed stdin, non-Bash tools, empty command)
  and a verification pass over `blocked.log`.
* Latest run: **97 passed, 0 failed** — full output in
  [`tests/results.txt`](tests/results.txt).

## Extending

Everything lives in the `RULE TABLES` at the top of `block_destructive.py`
and three small checkers, one per family: `check_rm`, `check_git`,
`check_sql`. To add a rule, add a pattern there and a line to each corpus,
then re-run the tests. To exempt `--force-with-lease` for your team, remove
it from `FORCE_PUSH_FLAGS` (see `BUILD-NOTES.md` for why it's blocked by
default).

## Limitations

This is a heuristic guardrail against accidents and over-eager automation,
not a security sandbox: a determined obfuscation (`eval`, base64 pipelines,
`python -c "os.system(...)"`, SQL built by string concatenation) can evade
pattern matching. Within its scope it fails safe in both directions — hook
bugs never break your session (unparseable input exits 0 silently), while a
positive match always blocks, even if logging fails.

## Uninstall

Remove `~/.claude/hooks/block_destructive.py` and delete the
`PreToolUse` entry from `~/.claude/settings.json` (or restore
`settings.json.bak`).

MIT licensed; do what you want with it.
