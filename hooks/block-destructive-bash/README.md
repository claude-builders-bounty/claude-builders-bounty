# block-destructive-bash

A Claude Code **PreToolUse** hook that stops destructive bash commands before
they run — and logs every attempt so you can see what Claude tried to do.

Blocks: `rm -rf`, `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA`, SQL `TRUNCATE`,
`DELETE FROM` without a `WHERE`, and `git push --force` (`--force-with-lease`
is allowed on purpose).

## Install in 2 commands

```bash
git clone https://github.com/<owner>/<repo> && cd <repo>/hooks/block-destructive-bash   # 1
bash install.sh                                                                        # 2
```

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py` and
merges the `PreToolUse` entry into `~/.claude/settings.json`, backing the file
up first. It is idempotent — running it twice updates the same entry.

Sanity check (no Claude session needed):

```bash
python3 ~/.claude/hooks/block_destructive_bash.py --check 'rm -rf /'    # DENY [rm_rf] ...
python3 ~/.claude/hooks/block_destructive_bash.py --check 'ls -la'      # ALLOW
```

## What Claude sees

When a command is blocked the hook returns a `permissionDecision: "deny"` with a
reason that names the risk and the safer alternative:

```
BLOCKED by block-destructive-bash [git_force_push]: `git push --force` rewrites
shared history and can erase other people's commits. Use
`git push --force-with-lease` (refuses when the remote moved), or push a new branch.
```

Claude gets that text instead of a silent tool failure, so it can pick a safe
path rather than retry the same command.

## Audit log

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`, one JSON
object per line:

```json
{"ts": "2026-11-26T10:12:33+08:00", "decision": "deny", "rule": "rm_rf", "cwd": "/Users/you/projects/api", "command": "rm -rf ./dist"}
```

Timestamp, attempted command and project path — enough to answer "what did the
agent try to delete last Tuesday, and in which repo?".
If the log cannot be written the hook still denies, it just warns on stderr.

## Rules and why

| Rule | Trigger | Why it is blocked |
|---|---|---|
| `rm_rf` | `rm` with recursive **and** force (`-rf`, `-fr`, `-r -f`, `--recursive --force`) | No recovery path, no prompt; a wrong path variable is unrecoverable |
| `drop_table` | `DROP TABLE/DATABASE/SCHEMA/VIEW/INDEX` | Drops schema and data; `IF EXISTS` makes it look routine, so it is not exempted |
| `truncate` | `TRUNCATE` in a SQL context (`TRUNCATE TABLE`, or any command mentioning `sqlite3`/`mysql`/`psql`…) | Not rollback-safe outside a transaction; coreutils `truncate -s` is left alone |
| `delete_without_where` | `DELETE FROM` with no `WHERE` in the same statement | Deletes every row; a missing predicate is usually an accident |
| `git_force_push` | `git push` with `--force`/`-f` or a `+refspec` | Rewrites shared history; `--force-with-lease` is allowed because it refuses stale remotes |

## Non-interference (the acceptance criterion that matters most)

- Only `tool_name == "Bash"` is inspected; `Write`, `Edit`, `Read`, MCP tools pass through.
- Normal commands exit silently: `rm -r dir` (no `-f`), `rm -f file`, `git push origin main`,
  `DELETE ... WHERE id = 3`, `truncate -s 0 app.log`, `npm test` — all allowed (tested).
- Any parse or logging failure **fails open**: a misbehaving hook must never wedge a session.
- Quoted strings are untouched: `git commit -m "rm -rf docs"` is not a match.
  Known limit: a destructive command split across an `eval`-built string is not
  pattern-matched — this is a guard-rail, not a sandbox.

## Escape hatch

Legitimate bulk deletes (build dirs) can be allow-listed without editing the hook:

```bash
export BLOCK_DESTRUCTIVE_BASH_ALLOW='rm -rf (node_modules|dist|\.next|build)'
```

Other environment switches:

| Variable | Default | Effect |
|---|---|---|
| `BLOCK_DESTRUCTIVE_BASH_MODE` | `json` | `exit2` = classic exit-code-2 blocking for older Claude Code builds |
| `BLOCK_DESTRUCTIVE_BASH_LOG` | `~/.claude/hooks/blocked.log` | alternate audit path |
| `BLOCK_DESTRUCTIVE_BASH_ALLOW` | unset | regex whitelist applied before rules |

## Tests

```bash
python3 -m unittest discover -s tests -v     # 8 tests, 26 command cases
```

Covers flag order (`-fr`), wrappers (`sudo rm -rf`), chained commands
(`cd x && rm -rf y`), multi-statement SQL, `--force-with-lease` false positives,
the JSON deny payload, log content, malformed input, and exit-code-2 mode.

Requires Python 3.7+, no third-party packages.
