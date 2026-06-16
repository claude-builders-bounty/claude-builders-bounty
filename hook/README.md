# Destructive Commands Guard

A Claude Code `pre-tool-use` hook that blocks dangerous bash commands before they execute.

## Installation (2 commands)

```bash
# 1. Install the hook
cp src/destructive-commands-guard.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/destructive-commands-guard.py

# 2. Configure Claude Code to use it
mkdir -p .claude && cp src/settings.json .claude/settings.json
```

Restart Claude Code. The hook is active immediately.

## What It Blocks

| Pattern | Danger |
|---|---|
| `rm -rf`, `rm --recursive --force` | Destructive recursive delete |
| `DROP TABLE` | Irreversible schema deletion |
| `git push --force` | Force push (overwrites remote history) |
| `TRUNCATE` | Bulk table clear |
| `DELETE FROM` (no `WHERE`) | Unrestricted row deletion |

## What It Allows

Normal commands (`ls`, `cd`, `git push`, `npm install`, `rm file.txt`, `DELETE FROM users WHERE id = ?`) pass through without interference.

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (ISO 8601)
- Project path
- Blocked command
- Reason

## Verification

```bash
# Test the hook outside Claude Code
echo '{"type":"Bash","params":{"command":"rm -rf /important"}}' | python3 ~/.claude/hooks/destructive-commands-guard.py
# Expected: exits code 2 with BLOCKED message on stderr

# Test a safe command
echo '{"type":"Bash","params":{"command":"ls -la"}}' | python3 ~/.claude/hooks/destructive-commands-guard.py
# Expected: exits code 0 silently
```
