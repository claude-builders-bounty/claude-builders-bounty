# Destructive-bash PreToolUse hook

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands
before they run, blocks them, and writes an audit line to
`~/.claude/hooks/blocked.log`.

## Install (2 commands or fewer)

From the repo root:

```bash
bash .claude/hooks/install.sh
```

The installer copies `block_destructive.py` into `~/.claude/hooks/` and merges
a `PreToolUse` matcher for `Bash` into your existing `~/.claude/settings.json`.
It does not overwrite unrelated settings and is idempotent (re-running it will
not add a duplicate entry).

## What it blocks

| Pattern | Why |
|---|---|
| `rm -rf` / `rm -fr` (any combined `-r…-f` form) | Recursive forced deletion |
| `DROP TABLE` | Destroys a database table |
| `TRUNCATE` | Empties a table irreversibly |
| `DELETE FROM` without a `WHERE` clause | Unbounded row deletion |
| `git push --force` | Overwrites remote history |
| `git reset --hard` | Discards uncommitted work |
| `git clean` without `-n`/`--dry-run` | Deletes untracked files |

Every other command passes through unchanged.

## Audit log

Blocked attempts append one JSON line to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-09-16T...Z","project_path":"/path/to/repo","command":"rm -rf /tmp/x","reason":"rm -rf recursive force deletion"}
```

## How it works

Claude Code pipes a hook event (JSON, including `tool_name` and
`tool_input.command`) to the script's stdin. A clean exit lets the command
run; exit code `2` stops it and shows Claude the reason on stderr, so it can
choose a safer approach.

## Manual test

```bash
echo '{"tool_input":{"command":"rm -rf ./build"},"project_path":"/tmp"}' | python3 .claude/hooks/block_destructive.py; echo "exit=$?"
```

Expect `exit=2` and a `BLOCKED:` message. Swap in `ls -la` and expect `exit=0`.

## Uninstall

Remove the `block_destructive.py` entry from the `PreToolUse` array in
`~/.claude/settings.json` and delete `~/.claude/hooks/block_destructive.py`.
