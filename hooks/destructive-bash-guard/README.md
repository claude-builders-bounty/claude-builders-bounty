# destructive-bash-guard

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands before they run.

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Irreversible DB operation |
| `TRUNCATE` | Wipes all table rows |
| `git push --force` / `-f` | Overwrites remote history |
| `DELETE FROM` without `WHERE` | Deletes every row in a table |

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with timestamp, reason, and project path.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
bash claude-builders-bounty/hooks/destructive-bash-guard/install.sh
```

That's it. The hook is registered in `~/.claude/settings.json` and active immediately.

## How it works

Claude Code calls the hook before every `Bash` tool use. The hook reads the command from stdin JSON, checks it against the blocked patterns, and — if dangerous — responds with a `deny` decision. Claude sees a clear explanation and cannot proceed. Normal commands pass through with zero overhead.

```
~/.claude/
  hooks/
    destructive-bash-guard.py   ← hook script
    blocked.log                  ← audit log
  settings.json                  ← hook registered here
```

## Uninstall

Remove the entry from `~/.claude/settings.json` and delete `~/.claude/hooks/destructive-bash-guard.py`.
