# pretooluse_bash_guard

A Claude Code **pre-tool-use hook** that intercepts destructive bash commands
before they run, tells Claude why, and logs every blocked attempt.

- Python 3, **standard library only** (no pip installs)
- Works on Linux/macOS/Windows (Git Bash or native Python)
- 52-case test suite (`python hook/tests/test_hook.py`)

## Install (2 commands)

```bash
git clone https://github.com/gwagwa2003/claude-builders-bounty.git .tmp-cbb && bash .tmp-cbb/hook/install.sh
```

That's it. The installer:

1. Copies the hook to `~/.claude/hooks/pretooluse_bash_guard.py`
2. Merges the hook entry into `~/.claude/settings.json` (backs up the original
   first, never clobbers existing hooks) — or creates it with this content:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [ { "type": "command", "command": "python3 ~/.claude/hooks/pretooluse_bash_guard.py" } ] }
    ]
  }
}
```

Manual install: copy `settings.snippet.json` contents into your
`~/.claude/settings.json` (merge with existing `hooks`).

## What it blocks

| Rule | Blocks | Examples |
|------|--------|----------|
| `rm-rf` | recursive + force `rm` in any flag order (`-rf`, `-fr`, `-Rf`, `-r -f`, `--recursive --force`), incl. behind `sudo`/`env`, in `&&`/`;`/`\|` chains | `rm -rf /`, `ls && rm -rf ~/data` |
| `drop-table` | `DROP TABLE` (any case, incl. `IF EXISTS`) | `mysql -e 'DROP TABLE users'` |
| `truncate` | `TRUNCATE [TABLE] <name>` | `psql -c 'TRUNCATE TABLE logs'` |
| `delete-no-where` | `DELETE FROM <t>` with **no WHERE clause** in the statement | `sqlite3 app.db 'DELETE FROM users;'` |
| `git-push-force` | `git push --force` / `-f` (combined short flags too) | `git push -f origin main`, `git push -uf origin main` |

On a match the hook:

- exits **2** (Claude Code blocks the command) and prints the reason on
  **stderr**, which Claude reads and adapts to
- also prints `{"decision":"block","reason": ...}` on stdout for newer clients
- appends one JSON line per rule to `~/.claude/hooks/blocked.log`:

```json
{"ts": "2026-09-16T19:29:17+00:00", "command": "git push --force origin main", "cwd": "/home/dev/app", "rule": "git-push-force", "segment": "git push --force origin main"}
```

## Sensible defaults (what it does NOT block)

- `git push --force-with-lease` — the safe force variant is allowed
- `rm -rf node_modules`, `rm -rf ./build`, `rm -rf dist`, `rm -rf .next`,
  `rm -rf __pycache__`, `rm -rf .venv`, etc. — well-known disposable build
  dirs are allowlisted (set `HOOK_ALLOW_SAFE_RM_TARGETS=0` to block all)
- `rm file.txt`, `rm -r dir`, `rm -f file` — recursive **and** force must both
  be present
- `DELETE FROM t WHERE ...`, `DROP INDEX ...`, `SELECT ...` — fine
- every non-Bash tool call passes through untouched (exit 0)

## Configuration (environment)

| Variable | Default | Effect |
|----------|---------|--------|
| `HOOK_DISABLE_RULES` | — | comma list of rule ids to disable, e.g. `truncate,rm-rf` |
| `HOOK_ALLOW_SAFE_RM_TARGETS` | `1` | `0` blocks every recursive+force `rm` |
| `HOOK_BLOCKED_LOG` | `~/.claude/hooks/blocked.log` | override log path |

## Demo (real captured runs)

Blocked — `git push --force origin main`:

```
$ echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"git push --force origin main"},"cwd":"/home/dev/app"}' | python3 pretooluse_bash_guard.py
{"decision": "block", "reason": "BLOCKED (git-push-force): `git push --force` rewrites shared history. Use `git push --force-with-lease` instead."}
# exit code: 2
# stderr (shown to Claude):
BLOCKED (git-push-force): `git push --force` rewrites shared history. Use `git push --force-with-lease` instead.
```

Blocked — `rm -rf /`:

```
$ echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"rm -rf /"},"cwd":"/home/dev/app"}' | python3 pretooluse_bash_guard.py
{"decision": "block", "reason": "BLOCKED (rm-rf): recursive+force rm is destructive. Use a plain non-recursive `rm <path>`, or target an allowlisted directory such as `rm -rf node_modules`."}
# exit code: 2
```

Allowed — `npm test`:

```
$ echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"npm test"},"cwd":"/home/dev/app"}' | python3 pretooluse_bash_guard.py
# (no output)
# exit code: 0
```

Resulting `blocked.log`:

```
{"ts": "2026-09-16T19:29:17.441021+00:00", "command": "git push --force origin main", "cwd": "/home/dev/app", "rule": "git-push-force", "segment": "git push --force origin main"}
{"ts": "2026-09-16T19:29:17.485151+00:00", "command": "rm -rf /", "cwd": "/home/dev/app", "rule": "rm-rf", "segment": "rm -rf /"}
```

## How it parses

Commands are split into quote-aware segments on `;`, `&&`, `||`, `|`, backticks
and `$()`. Each segment is tokenized with `shlex` (so `rm "-rf" /weird` and
`sudo rm -rf /` are handled), and `rm`/`git push` rules inspect token flags.
SQL rules scan the fully-unquoted command line — deliberately conservative:
`echo "DROP TABLE x"` is blocked too, because a false positive costs one retry
while a false negative costs a table. Malformed stdin or non-Bash payloads
always pass through (exit 0).

## Tests

```bash
python3 hook/tests/test_hook.py     # or: python3 -m unittest discover -s hook/tests -v
```

52 tests cover every rule positive/negative, flag permutations, quote tricks,
command chains, `sudo`/`env` wrappers, the safe-variant allowlists, rule
disabling, log-file contents, and non-Bash passthrough.

## Files

```
hook/
├── pretooluse_bash_guard.py   # the hook (stdlib only)
├── install.sh                 # 2-command installer (merges settings.json safely)
├── settings.snippet.json      # the hook config, for manual install
├── README.md
└── tests/test_hook.py         # 52-case unittest suite
```
