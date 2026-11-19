# pre-tool-use — Claude Code destructive-command blocker

Stops Claude from running `rm -rf`, `DROP TABLE`, `git push --force` and other
irreversible commands before they execute — and tells it why.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/pre-tool-use.py https://raw.githubusercontent.com/breezesamuel/claude-builders-bounty/bounty-003-helium/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

## Configure Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      { "command": "~/.claude/hooks/pre-tool-use.py" }
    ]
  }
}
```

## Test locally

```bash
echo '{"tool":"bash","arguments":{"command":"rm -rf /tmp/test"}}' | ~/.claude/hooks/pre-tool-use.py; echo "exit=$?"
```

Expected output: stderr explains why; exit code 1; logs to `~/.claude/hooks/blocked.log`.

## What it blocks

| Pattern | Blocked |
|---|---|
| `rm -rf <path>` (recursive force delete) | ✅ |
| `git push --force`, `git push --delete`, `git reset --hard` | ✅ |
| `DROP TABLE`, `DROP DATABASE`, `TRUNCATE` | ✅ |
| `DELETE FROM <table>` without WHERE | ✅ |
| `chmod -R 777`, `mkfs`, `dd if=/dev/zero` | ✅ |

## Logs

Every block appends to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-11-19T11:58:00Z","command":"rm -rf /tmp/test","project_path":"/home/dev/myapp","reason":"rm -rf / recursive force delete"}
```

## Behavior

- Normal bash commands pass through unchanged (exit 0).
- Blocked commands are NOT executed; the model gets a clear explanation via stderr so it can propose a safer alternative.
