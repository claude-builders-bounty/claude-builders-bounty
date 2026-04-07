# Claude Code Pre-Tool-Use Hook

Blocks destructive bash commands before they execute.

## Installation (2 commands)

```bash
# Install the hook
curl -fsSL https://raw.githubusercontent.com/YOUR_USER/claude-builders-bounty/main/hooks/pre-tool-use -o ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use

# Verify
python3 ~/.claude/hooks/pre-tool-use
```

## Patterns Blocked

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Recursive delete |
| `DROP TABLE` | Destroys data |
| `TRUNCATE` | Deletes all rows |
| `DELETE FROM` without WHERE | Risks data loss |
| `git push --force` | Overwrites history |
| `DROP DATABASE` | Destroys database |

## Log Location

All blocked attempts logged to: `~/.claude/hooks/blocked.log`

## Example Log Entry

```
[2026-04-07T18:32:00] BLOCKED | rm -rf — recursive delete | /path/to/project | rm -rf /tmp/test
```

## Disable (if needed)

```bash
chmod -x ~/.claude/hooks/pre-tool-use
```
