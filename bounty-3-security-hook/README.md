# guard-hook: Claude Code Destructive Command Blocker

A `PreToolUse` security hook for Claude Code that intercepts and blocks dangerous bash commands before they execute.

## What it blocks

| Pattern | Example | Why |
|---|---|---|
| `rm -rf` | `rm -rf /`, `rm -rf .` | Irreversible recursive deletion |
| `DROP TABLE` | `DROP TABLE users;` | Permanent database table destruction |
| `git push --force` | `git push --force origin main` | Rewrites remote history |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | Removes all rows without logging |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` | Unconditional row deletion |

Allowed through: `DELETE FROM users WHERE id = 5;` (has a WHERE clause).

## Install (2 commands)

```bash
cp guard-hook.sh ~/.claude/hooks/guard-hook.sh && chmod +x ~/.claude/hooks/guard-hook.sh
cat hooks-config.json >> ~/.claude/settings.json
```

> If `~/.claude/settings.json` already has a `hooks` key, merge the `PreToolUse` entry manually instead of appending.

## How it works

1. Claude Code fires a `PreToolUse` event before every Bash tool call.
2. The hook reads JSON from stdin containing `tool_input.command` and `cwd`.
3. Each command is checked against regex patterns for the five blocked categories.
4. **If blocked**: logs to `~/.claude/hooks/blocked.log`, exits with code 2, and prints a clear reason to stderr (which Claude sees as feedback).
5. **If safe**: exits with code 0 silently. No interference with normal commands.

## Log format

Every blocked attempt is logged as a JSON line to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-03-26T14:30:00Z","rule":"BLOCKED_RM_RF","command":"rm -rf /tmp/data","project":"/home/user/myproject"}
```

Fields: `timestamp` (UTC ISO 8601), `rule` (which pattern matched), `command` (the blocked command), `project` (working directory).

## Verify it works

Test the hook manually by piping mock JSON:

```bash
# Should be blocked (exit code 2, message on stderr):
echo '{"tool_input":{"command":"rm -rf /"},"cwd":"/tmp"}' | ~/.claude/hooks/guard-hook.sh
echo "Exit code: $?"

# Should be allowed (exit code 0, no output):
echo '{"tool_input":{"command":"ls -la"},"cwd":"/tmp"}' | ~/.claude/hooks/guard-hook.sh
echo "Exit code: $?"
```

Run `/hooks` inside Claude Code to confirm the hook appears under `PreToolUse > Bash`.

## Dependencies

- **bash** (4.0+)
- **jq** (recommended; falls back to grep/sed if unavailable)
- **grep** with `-E` (extended regex)

## Uninstall

```bash
rm ~/.claude/hooks/guard-hook.sh
```

Then remove the `PreToolUse` entry from `~/.claude/settings.json`.

## License

MIT
