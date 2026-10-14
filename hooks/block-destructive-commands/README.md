# block-destructive — a Claude Code PreToolUse hook

Stops Claude Code **before** it runs a destructive shell command, tells it why, and
keeps an audit log of every attempt.

Works as a `PreToolUse` hook for the `Bash` (and `PowerShell`) tool: it reads the hook
payload on stdin, inspects `tool_input.command`, and returns a `deny` decision with a
clear reason when the command matches a destructive pattern. Everything else exits
silently, so normal Bash calls are completely unaffected.

## Install (2 commands)

```bash
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive-commands/install.sh | bash
```

That is command 1 and it is enough: the script copies the hook to
`~/.claude/hooks/block-destructive.sh`, merges the `PreToolUse` entry into
`~/.claude/settings.json` (keeping a `.bak`) and prints a one-line self-test.
Then restart Claude Code so it reloads the configuration:

```bash
# command 2 (optional): verify the hook blocks something
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"'$PWD'"}' | ~/.claude/hooks/block-destructive.sh
```

Prefer manual install? Two commands:

```bash
mkdir -p ~/.claude/hooks && cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh
# then add the snippet below to ~/.claude/settings.json
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|PowerShell",
        "hooks": [
          { "type": "command", "command": "/home/YOU/.claude/hooks/block-destructive.sh", "args": [] }
        ]
      }
    ]
  }
}
```

## What it blocks

| Pattern | Examples caught |
| --- | --- |
| Recursive force delete | `rm -rf build`, `rm -fr dist`, `rm -r -f dir`, `rm --recursive --force dir`, `sudo rm -rf /var/data` |
| `DROP TABLE` | `psql -c "DROP TABLE users"` |
| `TRUNCATE` | `mysql -e "TRUNCATE TABLE orders"` |
| `DELETE FROM` without `WHERE` | `psql -c "DELETE FROM users"`, and per statement in `echo x; DELETE FROM logs; SELECT 1` |
| Force push | `git push --force origin main`, `git push -f` |

## What it deliberately allows

`ls`, `rm file.txt`, `rm -r ./build` (no force), `DELETE FROM users WHERE id = 1`,
`git push origin main`, `git push --force-with-lease` (the safe variant), and any
tool call that is not Bash/PowerShell. If a command does not match, the hook prints
nothing and exits `0`, so Claude Code's normal permission flow applies.

## Log

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` (override the
directory with `CLAUDE_HOOK_LOG_DIR`):

```text
2026-10-14T13:51:16Z | rm recursive+force | /home/dev/project | rm -rf /tmp/build
2026-10-14T13:51:17Z | DELETE without WHERE | /home/dev/project | psql -c "DELETE FROM users"
2026-10-14T13:51:17Z | git push --force | /home/dev/project | git push -f
```

Format: `ISO-8601 UTC | pattern | project path (cwd) | attempted command`.

## What Claude sees

The decision is returned in the documented shape, so Claude gets the reason and can
adapt (for example, deleting a specific file instead of a tree):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked by the block-destructive hook: this is a recursive force delete (rm -rf). Nothing was executed. If the deletion is really intended, ask the user to run it themselves, or re-run the session with CLAUDE_ALLOW_DESTRUCTIVE=1."
  }
}
```

## Escape hatch

```bash
CLAUDE_ALLOW_DESTRUCTIVE=1 claude    # disables the block for that session
```

## Tests

```bash
bash test/run-tests.sh
```

19 payload cases (11 that must be denied, 8 that must pass, including non-Bash tools)
plus checks on the log format and the escape hatch. Current result:

```text
RESULTADO: 23 pasaron, 0 fallaron
```

## Notes and known limits

- No dependencies beyond `bash` plus one of `jq`, `python3` or `node` to read the
  payload (it uses whichever is present, no install required).
- The SQL patterns are matched textually, so a command that merely *quotes* one of
  them (`echo "DROP TABLE"`, `grep "rm -rf" notes.md`) is also blocked. That is
  intentional — a false block is recoverable, an executed `DROP TABLE` is not — and
  `CLAUDE_ALLOW_DESTRUCTIVE=1` covers legitimate cases.
- `rm -r` without `-f` is not blocked; the requested pattern is the recursive *force*
  delete.

MIT, like the rest of this repository.
