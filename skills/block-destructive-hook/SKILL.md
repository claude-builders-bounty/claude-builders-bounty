# SKILL.md — Block Destructive Commands Hook

## What this skill does

A Claude Code `pre-tool-use` hook in Python that intercepts and blocks dangerous bash commands before they execute.

## Hook Installation

Place `scripts/block_destructive.py` in:
```
~/.claude/hooks/block_destructive.py
```

Make it executable:
```bash
chmod +x ~/.claude/hooks/block_destructive.py
```

## Patterns blocked

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Recursive force delete |
| `DROP TABLE` | Database drop |
| `TRUNCATE TABLE` | Database truncate |
| `git push --force` | Force push |
| `DELETE FROM table;` | DELETE without WHERE clause |
| `shred` | Secure deletion |
| `dd of=/dev/` | Direct disk write |

## Output

- Blocked commands are logged to `~/.claude/hooks/blocked.log`
- A clear error message is displayed in Claude Code output
- Safe commands pass through unchanged

## Testing

```bash
# This should be blocked:
rm -rf /tmp/test

# This should pass:
rm -rf /tmp/test --dry-run
```