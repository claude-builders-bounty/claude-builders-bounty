# Pre-tool-use Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts dangerous shell and SQL commands
**before** they execute, logs every blocked attempt, and tells Claude exactly why
it was blocked and what to do instead.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use.d
cp hook.py ~/.claude/hooks/pre-tool-use.d/block-destructive.py && chmod +x ~/.claude/hooks/pre-tool-use.d/block-destructive.py
```

That's it. Claude Code picks up hooks automatically on the next session.

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf …` / `rm -fr …` | Recursively destroys files with no undo |
| `DROP TABLE / DATABASE / SCHEMA` | Permanently deletes database objects |
| `git push --force` / `git push -f` | Rewrites remote history, can destroy teammates' work |
| `TRUNCATE TABLE …` | Deletes every row instantly, no WHERE clause |
| `DELETE FROM … ;` (no WHERE) | Deletes every row in the table |

`--force-with-lease` is explicitly **not** blocked (it is safe).

## Log Format

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
[2026-03-29T12:00:00+00:00] BLOCKED
  project : /Users/you/myproject
  reason  : rm -rf destroys files recursively and irreversibly
  command : 'rm -rf /tmp/build'
```

## What Claude Sees When Blocked

```
BLOCKED: rm -rf destroys files recursively and irreversibly

The command you attempted has been blocked by the safety hook.
Attempted: 'rm -rf /tmp/build'

Consider a safer alternative:
  - For file deletion: move to trash or use `rm` without -rf
  - For SQL deletes: add a WHERE clause
  - For git force push: use --force-with-lease instead
  - For DROP: create a backup first (pg_dump / mysqldump)

This block has been logged to: /Users/you/.claude/hooks/blocked.log
```

## Running Tests

```bash
python3 test_hook.py
```

18 tests covering both blocked and allowed patterns (including edge cases like
`--force-with-lease`, `DELETE FROM … WHERE`, interactive `rm`).

## How It Works

The hook reads a JSON payload from stdin:

```json
{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}
```

- Exit code `0` → allow
- Exit code `2` → block (stdout is forwarded to Claude as the reason)

Only `Bash` tool calls are inspected. All other tools pass through unchanged.
The hook is pure Python 3 stdlib — no dependencies.
