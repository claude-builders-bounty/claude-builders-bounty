# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `PreToolUse` hook that stops dangerous bash commands **before**
they run — and tells Claude exactly why.

Bounty: [claude-builders-bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) — **$100 (Opire)**

## What it blocks

| Pattern | Example | Result |
|---|---|---|
| `rm -rf` and variants | `rm -rf /tmp/x`, `rm -fr`, `rm -r -f`, `rm --recursive --force`, `sudo rm -rf …` | Blocked |
| `rm -r` of `/`, `~`, `*`, `.` | `rm -r /` | Blocked |
| `DROP TABLE` | `DROP TABLE users`, `drop table if exists users` | Blocked |
| `git push --force` / `-f` | `git push --force origin main`, `git push -f` | Blocked |
| `TRUNCATE` | `TRUNCATE TABLE users` | Blocked |
| `DELETE FROM` without `WHERE` | `DELETE FROM users` | Blocked |

## What it deliberately allows

- `rm file.txt`, `rm -r dir` (no `-f`), `rm -f file.txt` (no `-r`)
- `git push origin main`, and **`git push --force-with-lease`** — the safe
  alternative to `--force`, so it is explicitly *not* blocked
- `DELETE FROM users WHERE id = 1` — a `WHERE` clause makes it safe
- `echo "rm -rf /"` — quoted text is not a command being run
- Every normal command: `ls`, `git status`, `npm test`, `SELECT …`, etc.

Chained commands are checked segment by segment, so
`ls && rm -rf /tmp/x` is still blocked.

## Install — 2 commands

```sh
./install.sh
```

That's it. The installer copies the hook to `~/.claude/hooks/`,
makes it executable, and registers it in `~/.claude/settings.json`
as a `PreToolUse` hook for `Bash`.

Manual install (also 2 commands):

```sh
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-commands.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-commands.py
# then add the PreToolUse entry from settings.example.json to ~/.claude/settings.json
```

## How it works

Claude Code sends the hook a JSON object on stdin for every `Bash` call:

```json
{"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}, "cwd": "/path/to/project"}
```

The hook replies with JSON on stdout:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "Blocked destructive command: rm with recursive (-r) and force (-f) flags is blocked. …"}}
```

Allowed commands get `"permissionDecision": "allow"`. Non-Bash tools and
malformed input are allowed (fail-open) so the hook can never break
Claude Code.

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
2026-11-26T12:00:00Z | cwd=/tmp/myproject | reason=rm with recursive (-r) and force (-f) flags is blocked | command=rm -rf /tmp/x
```

Set `HOOK_BLOCKED_LOG=/tmp/test.log` to override the log path (used by tests).

## Try it without Claude Code

```sh
python3 hooks/block-destructive-commands.py --check "rm -rf /tmp/x"   # BLOCKED
python3 hooks/block-destructive-commands.py --check "ls -la"          # ALLOWED
echo '{"tool_name": "Bash", "tool_input": {"command": "DELETE FROM users"}, "cwd": "/tmp"}' \
  | python3 hooks/block-destructive-commands.py
```

## Tests

```sh
python3 -m pytest tests/ -v
# or: python3 -m unittest discover -s tests -v
```

36 tests: blocked vs allowed cases for `rm`, `git push`, SQL, normal
commands, plus end-to-end hook-protocol tests (deny JSON, allow JSON,
non-Bash tools, malformed input, log contents).

## Files

| File | What it is |
|---|---|
| `hooks/block-destructive-commands.py` | The hook (Python 3.8+, stdlib only) |
| `hooks/block-destructive-commands.sh` | Bash fallback — runs the Python hook, or a grep check if Python is missing |
| `install.sh` | One-command installer |
| `settings.example.json` | Example `~/.claude/settings.json` hook entry |
| `tests/test_block_destructive_commands.py` | 36-test suite |

## Notes / limitations

- `git push --force-with-lease` is allowed by design (see above).
- SQL inside a quoted string passed to a SQL client (`psql -c "DROP TABLE …"`)
  is blocked; SQL quoted inside `echo`/`grep` is not.
- The hook checks the command text, not what a script it calls might do
  (`./unknown-script.sh` is allowed — it cannot be inspected statically).
