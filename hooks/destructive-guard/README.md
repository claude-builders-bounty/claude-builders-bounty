# Claude Code — Destructive Command Guard

A `pre-tool-use` hook for Claude Code that intercepts dangerous bash commands before they execute.

## Install

```bash
cp hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

That's it. Claude Code loads hooks automatically from `~/.claude/hooks/`.

## What it blocks

| Pattern | Reason |
|---|---|
| `rm -rf` | Recursive force delete — unrecoverable |
| `DROP TABLE` | Irreversible schema destruction |
| `TRUNCATE` | Wipes entire table |
| `DELETE FROM` without `WHERE` | Deletes all rows |
| `git push --force` / `-f` | Rewrites remote history |
| `dd if=... of=/dev/...` | Overwrites block device |
| `mkfs` | Formats/destroys filesystem |
| `chmod -R 777` | World-writable permissions |

## What it logs

Every blocked attempt is written to `~/.claude/hooks/blocked.log`:

```
[2026-04-04T00:00:00Z] BLOCKED | reason="rm -rf: recursive force delete" | project="/home/user/myapp" | cmd="rm -rf node_modules"
```

## How it works

Claude Code runs this script before every `Bash` tool call. The hook reads the command from stdin (JSON), checks it against the blocked patterns, and either:
- Returns `{"decision": "block", "reason": "..."}` — Claude is told why and stops
- Exits 0 silently — command runs normally

Normal commands pass through with zero overhead.
