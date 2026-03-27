# Pre-Tool-Use Guard Hook

Blocks dangerous bash commands before Claude Code executes them.

## Install (1 command)

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use-guard.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use-guard.sh
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "bash",
        "command": "bash ~/.claude/hooks/pre-tool-use-guard.sh"
      }
    ]
  }
}
```

## What It Blocks

- `rm -rf /` / `rm -rf ~` — Recursive root/home deletion
- `DROP TABLE` / `TRUNCATE` — Database destruction
- `git push --force` — Force push (history rewrite)
- `DELETE FROM` — Mass data deletion
- `mkfs` / `dd if=` — Disk formatting
- `chmod -R 777 /` — Permission destruction
- Fork bombs

## How It Works

1. Reads tool input from stdin (Claude Code hooks format)
2. Checks command against dangerous patterns
3. Blocks and logs to `~/.claude/hooks/blocked.log`
4. Returns `{decision: "block", reason: "..."}` or `{decision: "allow"}`
