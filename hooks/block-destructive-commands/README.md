# block-destructive-commands

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they execute.

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -fr` | Recursive force delete — irreversible |
| `DROP TABLE` / `DROP DATABASE` | Wipes database tables/databases |
| `TRUNCATE` | Deletes all rows in a table |
| `DELETE FROM` without `WHERE` | Deletes every row |
| `git push --force` / `-f` | Overwrites remote git history |
| `git reset --hard` | Discards all uncommitted changes |
| `chmod -R 777` | Insecure recursive permission change |
| `dd to /dev/sd*` | Can wipe entire disk |
| `mkfs` | Formats/wipes a filesystem |
| `shred` | Irreversible file destruction |

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, reason, and project path.

## Install

```bash
cp hook.py ~/.claude/hooks/block-destructive-commands.py
chmod +x ~/.claude/hooks/block-destructive-commands.py
```

Then add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive-commands.py"
          }
        ]
      }
    ]
  }
}
```

## How it works

Claude Code calls this hook with a JSON payload before every `Bash` tool use. The hook checks the command against a list of dangerous patterns using regex. If matched:

1. Logs the attempt to `~/.claude/hooks/blocked.log`
2. Returns `{"decision": "block", "reason": "..."}` — Claude Code shows the reason to the user
3. The command never runs

Safe commands pass through with a zero exit code (no output = allow).

## Log format

```
[2026-06-15 23:41:02] BLOCKED | project=/home/user/myapp | reason=rm -rf (recursive force delete) | cmd=rm -rf ./dist
```
