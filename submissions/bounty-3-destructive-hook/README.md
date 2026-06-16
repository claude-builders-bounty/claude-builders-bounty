# Destructive Command Guard — Bounty #3

Claude Code `PreToolUse` hook that blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.py
```

Merge `hooks.json.example` into your project's `.claude/settings.json` (or `~/.claude/settings.json`).

## Blocked patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Irreversible recursive delete |
| `DROP TABLE` | Drops database tables |
| `TRUNCATE` | Wipes table contents |
| `git push --force` / `-f` | Rewrites remote history |
| `DELETE FROM` without `WHERE` | Deletes all rows |

## Logging

Blocked attempts append JSON lines to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-06-16T12:00:00Z","command":"rm -rf /tmp/x","project_path":"/Users/dev/app"}
```

## Behavior

- **Blocked:** exit code `2`, explanation on stderr (Claude Code PreToolUse convention)
- **Allowed:** exit code `0`, no output
- **Non-Bash tools:** ignored

## Tests

```bash
./tests/test_hook.sh
```