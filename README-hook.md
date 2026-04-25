# safe-shell.sh 🔒

A Claude Code **pre-tool-use hook** that blocks destructive bash commands before they execute.

**Blocks:**
- `rm -rf` — recursive force delete
- `DROP TABLE` — irreversible SQL table destruction
- `git push --force` — destructive remote history rewrite
- `TRUNCATE` — irreversible SQL table emptying
- `DELETE FROM` without `WHERE` clause — mass row deletion

**Logs** every blocked attempt to `~/.claude/hooks/blocked.log`.

## Install

```bash
mkdir -p ~/.claude/hooks/ && cp safe-shell.sh ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

That's it. Restart Claude Code and you're protected.

## How it works

Claude Code calls the hook before executing every `Bash` tool. The hook inspects the command and returns `{"approved": false}` with an explanation if it matches a dangerous pattern. Normal commands pass through uninterrupted.

## Logs

Blocked attempts are logged at `~/.claude/hooks/blocked.log`:
```
[2026-04-25 12:00:00] Blocked: 'rm -rf' — recursive force delete is destructive and irreversible.
  Project: /home/user/my-project
  Command: rm -rf /var/log/*.db
  ---
```
