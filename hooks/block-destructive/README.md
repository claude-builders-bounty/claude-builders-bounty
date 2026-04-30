# 🛡️ Destructive Command Blocker — Claude Code Pre-Tool-Use Hook

Intercepts dangerous bash commands **before** Claude executes them, logs every blocked attempt, and explains the block clearly to Claude so it can course-correct.

## Blocked Patterns

| Pattern | Why |
|---|---|
| `rm -rf` / `rm -fr` | Recursive force-delete — irreversible |
| `DROP TABLE` | Destroys a database table |
| `TRUNCATE` | Wipes all rows from a table |
| `DELETE FROM` without `WHERE` | Deletes every row |
| `git push --force` / `-f` | Overwrites remote history |

## Install (2 commands)

```bash
cp block-destructive.py ~/.claude/hooks/block-destructive.py && chmod +x ~/.claude/hooks/block-destructive.py
```

```bash
cp settings.json ~/.claude/settings.json   # or merge into existing settings.json
```

That's it. Claude Code will now intercept all Bash tool calls through the hook.

## What happens on a blocked command

1. The command **does not execute**
2. A log entry is written to `~/.claude/hooks/blocked.log`:
   ```
   2026-04-30T14:22:01 | BLOCKED | reason='rm -rf (recursive force delete)' | project='/home/user/myapp' | command='rm -rf dist/'
   ```
3. Claude sees a clear explanation:
   ```
   🚫 BLOCKED by safety hook
   Reason : rm -rf (recursive force delete)
   Command: 'rm -rf dist/'

   This command has been blocked because it can cause irreversible data loss.
   If you genuinely need to run a destructive operation, please ask the user to
   do it manually after reviewing the consequences.
   ```

## Normal commands are unaffected

`ls`, `mkdir`, `cat`, `git status`, `npm install` — all pass through instantly with zero overhead.

## Requirements

- Python 3.8+ (no third-party dependencies)
- Claude Code with hooks support
