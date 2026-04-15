# HOOK: Block Destructive Bash Commands in Claude Code

> Bounty #3 — $100 | [Issue Link](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

## Install (2 commands)

```bash
# 1. Copy the hook script
cp block-destructive.py ~/.claude/hooks/block-destructive.py

# 2. Add to your Claude Code settings (~/.claude/settings.json)
# Add this to the "hooks" section:
```

Add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

Done. Claude Code will now check every bash command before execution.

## What it blocks

| Pattern | Severity | Why |
|---------|----------|-----|
| `rm -rf` | CRITICAL | Recursive force delete — can wipe entire directories |
| `DROP TABLE` / `DROP DATABASE` | CRITICAL | Permanently deletes database objects |
| `TRUNCATE` | CRITICAL | Deletes all rows without logging |
| `DELETE FROM` without `WHERE` | CRITICAL | Deletes all rows — missing WHERE clause |
| `git push --force` / `-f` | HIGH | Overwrites remote history |
| `git reset --hard` | HIGH | Discards all uncommitted changes |
| `git clean -f` | HIGH | Permanently deletes untracked files |
| `chmod 777` | HIGH | World-writable permissions — security risk |
| `mkfs` / `format` | CRITICAL | Formats disk partition |
| `dd if=` | CRITICAL | Raw disk write |
| `> /dev/sda` | CRITICAL | Direct device write |
| `kill -9 -1` | CRITICAL | Kills ALL user processes |
| Fork bomb `:(){ :\|:& };:` | CRITICAL | Crashes system |

## What it does NOT block

- `rm file.txt` (non-recursive, no -rf)
- `git push` (normal push without --force)
- `DELETE FROM users WHERE id = 5` (has WHERE clause)
- `chmod 755` (reasonable permissions)
- All other safe bash commands pass through normally

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` in JSON format:

```json
{
  "timestamp": "2026-04-15T14:30:00",
  "command": "rm -rf /",
  "blocked_pattern": "rm -rf",
  "description": "Recursive force delete — can wipe entire directories",
  "severity": "critical",
  "project_path": "/home/user/my-project"
}
```

## Bonus features beyond requirements

- **13 patterns** instead of the required 5 (rm -rf, DROP, git push --force, TRUNCATE, DELETE + 8 more)
- **Severity levels** (CRITICAL / HIGH) for triage
- **git reset --hard** and **git clean -f** blocking (common accidental data loss)
- **Fork bomb detection**
- **chmod 777** blocking (security hardening)
- **JSON structured logging** with timestamp, command, project path
- **Fail-open design** — if the hook errors, commands still run (no false lockouts)
- **Clear error messages** explaining WHY a command was blocked and what to do instead
- **Command truncation** in logs (prevents log bloat from huge commands)

## Files

| File | Purpose |
|------|---------|
| `block-destructive.py` | The hook script |
| `README.md` | This file |
