# block-destructive — PreToolUse hook for Claude Code

A small Python hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks)
that intercepts Bash tool calls and refuses any command matching a known
destructive pattern. Every blocked attempt is appended to an audit log so
you can see what Claude tried to do.

## Blocked patterns

| Pattern | Examples blocked |
|---|---|
| `rm -rf` (recursive **and** force) | `rm -rf /tmp/x`, `rm -fr build`, `rm --recursive --force node_modules`, `sudo rm -rf /` |
| SQL `DROP` statements | `DROP TABLE users`, `DROP DATABASE mydb;`, `drop schema if exists public`, `DROP TABLE IF EXISTS tmp_users` |
| `git push --force` | `git push --force origin main`, `git push -f`, `git push --force-with-lease`, `git push --force-if-includes` |
| `TRUNCATE` | `TRUNCATE TABLE events`, `truncate logs` |
| `DELETE FROM` without a `WHERE` clause | `DELETE FROM users;`, `DELETE FROM events` |

`rm -f file.txt` (force only), `rm -r directory` (recursive only), and
`rm -i file` (interactive) all pass through. The audit log only sees
truly destructive combinations.

## Install (2 commands)

```bash
# 1. Clone this repo (or download hooks/block-destructive.py + install.sh)
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
cd claude-builders-bounty/hooks

# 2. Run the installer — copies the hook to ~/.claude/hooks/ and
#    registers it in ~/.claude/settings.json as a PreToolUse matcher
bash install.sh
```

That's it. There is no `pip install`, no daemon, no build step. The hook
is one ~150-line Python 3 file with a small unit test corpus and an
integration test that exercises the actual subprocess.

## Verify it works

```bash
# Should print the rule that matched and exit 2:
python3 ~/.claude/hooks/block-destructive.py <<'JSON'
{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/tmp"}
JSON
echo "exit code: $?"

# Should exit 0 (allowed) with no output:
python3 ~/.claude/hooks/block-destructive.py <<'JSON'
{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -f file.txt"},"cwd":"/tmp"}
JSON
echo "exit code: $?"
```

Or, in a real Claude Code session, just ask Claude to run
`rm -rf /tmp/should-fail`. The hook will refuse and the attempt will be
appended to `~/.claude/hooks/blocked.log`.

## Audit log

Every block is appended as a single TSV line to the path in the
`DESTRUCTIVE_HOOK_LOG` env var (default `~/.claude/hooks/blocked.log`):

```
2026-06-12T15:42:11+00:00	/tmp/test-project	rm --recursive --force	rm -rf node_modules
2026-06-12T15:42:14+00:00	/tmp/test-project	git push --force	git push -f origin main
2026-06-12T15:42:18+00:00	/tmp/test-project	DELETE FROM without WHERE	DELETE FROM events;
```

The hook never panics or throws on logging failures — a missing log file
just means a blocked command was silently allowed, not that Claude was
locked out. The hook also fails **open** on a malformed JSON payload, so
a broken Claude Code update can't freeze your session.

## Tests

```bash
# Unit tests for the pattern matchers (no subprocess, fast)
python3 hooks/test_block_destructive.py

# Integration tests that spawn the hook as a real subprocess
python3 hooks/test_integration.py
```

Both ship with the repo and run in under a second on any machine with
Python 3.10+. No external dependencies.

## Files

```
hooks/
├── block-destructive.py        # the hook (the only file the user installs)
├── install.sh                  # one-line installer
├── test_block_destructive.py   # unit tests for match_rule()
├── test_integration.py         # spawn-the-hook subprocess tests
└── README.md                   # this file
```

## Why these patterns and not others

The criteria in the bounty listed five specific destructive patterns.
This hook implements those literally and resists false positives by:

- Requiring **both** recursive and force flags on `rm` (so `rm -r` and
  `rm -f` independently remain allowed).
- Not stripping string literals before matching — `psql -c 'DROP TABLE
  users'` should still be blocked even though the SQL sits inside a
  string. The cost is that `echo "rm -rf"` is also blocked; the user can
  pipe that through `cat` or write it to a file first.
- Stripping only SQL line and block comments before evaluating
  `DELETE FROM`, so that `WHERE /* kept */ 1=1` is correctly recognised
  as having a `WHERE` clause.

## License

MIT (matches the rest of the repo).
