Resolves #3

## What

A Claude Code `PreToolUse` hook (Python) that intercepts destructive bash commands **before** they execute, blocks them, returns a clear reason to Claude, and logs the attempt.

## Blocks

- `rm -rf` / `rm -fr` (recursive force delete, including absolute paths)
- `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` / `DROP INDEX` / `DROP VIEW` / `DROP FUNCTION` / `DROP PROCEDURE`
- `TRUNCATE` (with or without `TABLE` keyword)
- `DELETE FROM <table>` without `WHERE` clause
- `git push --force` / `git push -f` (including `--force-with-lease`)

## Allows

Normal bash like `ls`, `cd`, `npm install`, `git status`, `git push origin main`, `rm file.txt`, `DELETE FROM users WHERE id=5` (with WHERE), `git push --force-with-lease` (covered above to be safe).

## How it works

1. Hook receives JSON payload from Claude Code via stdin
2. Filters by `tool_name == "Bash"` (other tools pass through)
3. Matches the command string against compiled regex patterns
4. On match: appends a structured `BLOCKED:` entry to `~/.claude/hooks/blocked.log`, then prints `{"decision": "block", "reason": "..."}` to stdout
5. Claude receives the reason and can ask the user for confirmation

## Files

- `hooks/pre-tool-use-block-destructive.py` — main hook (Python 3.7+, ~100 lines, no third-party deps)
- `hooks/README.md` — installation in 2 steps, log format, customization
- `hooks/samples/test-payload.json` — test fixture

## Installation (2 steps)

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use-block-destructive.py ~/.claude/hooks/
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py"}
        ]
      }
    ]
  }
}
```

## Tested

Six scenarios all pass:

| Command | Result |
|---|---|
| `rm -rf /tmp/foo` | blocked (recursive force delete on absolute path) |
| `ls -la` | allowed |
| `DROP TABLE users;` | blocked (SQL DROP) |
| `git push --force origin main` | blocked (force push) |
| `DELETE FROM users WHERE id=5;` | allowed (has WHERE) |
| `TRUNCATE TABLE logs` | blocked (TRUNCATE) |

## Log format

```text
[2026-06-18T08:55:00] BLOCKED: SQL DROP statement
  command: DROP TABLE users;
  project: /tmp

[2026-06-18T08:56:12] BLOCKED: rm with -r and -f flags
  command: rm -rf node_modules
  project: /home/user/project
```

## Bounty

$100 via Opire
