# Block Destructive Bash Commands — Claude Code Pre-Tool-Use Hook

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands **before they execute**.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use.py https://raw.githubusercontent.com/ninonorden/claude-builders-bounty/feat/destructive-command-hook/hooks/block_destructive.py
```

Then add to `~/.claude/settings.json` (create if missing):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python3 ~/.claude/hooks/pre-tool-use.py"
      }
    ]
  }
}
```

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` / `rm -fr` | Recursive force delete — permanent |
| `git push --force` / `-f` / `--force-with-lease` | Rewrites remote history |
| `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` | Permanent data destruction |
| `TRUNCATE` | Removes all rows |
| `DELETE FROM` without `WHERE` | Unscoped delete — removes every row |
| `chmod -R 777` | Opens all permissions — security risk |
| Fork bombs `:(){ :|:& };:` | Would crash the system |
| `mkfs.*` / `dd of=/dev/*` | Filesystem format / disk wipe |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
2026-10-01T14:22:01	BLOCKED	rm -rf /tmp/test	project=/Users/me/myproject	reason=Recursive force delete...
```

## Safe commands pass through unchanged

Normal bash commands (`ls`, `git status`, `npm install`, etc.) are not affected.
The hook exits 0 silently for anything that is not a Bash tool call.

## Disable temporarily

```bash
mv ~/.claude/hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py.disabled
```

## Tests

```bash
# Run the unit tests
python3 tests/test_hook.py
```

All 12 test cases pass:
- ✅ `rm -rf /tmp` → blocked
- ✅ `rm -fr /var` → blocked
- ✅ `rm --recursive --force .` → blocked
- ✅ `git push --force` → blocked
- ✅ `git push -f origin main` → blocked
- ✅ `DROP TABLE users` → blocked
- ✅ `TRUNCATE sessions` → blocked
- ✅ `DELETE FROM logs` (no WHERE) → blocked
- ✅ `chmod -R 777 /app` → blocked
- ✅ `ls -la` → allowed ✓
- ✅ `git push origin main` → allowed ✓
- ✅ `DELETE FROM logs WHERE id > 1000` → allowed ✓
