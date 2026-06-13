# Pre-Tool-Use Blocker

> A Claude Code pre-tool-use hook that intercepts and blocks destructive
> bash commands before they execute.

## What it blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /tmp/*` | Accidental recursive deletion |
| `git push --force` / `-f` | `git push origin main -f` | Overwrites remote history |
| `DROP TABLE` / `DATABASE` / etc. | `DROP TABLE users` | Irreversible schema loss |
| `TRUNCATE` | `TRUNCATE users` | Wipes all rows instantly |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Removes every row without recovery |

## Install

```bash
# 1. Clone/copy this directory into your Claude Code hooks folder
mkdir -p ~/.claude/hooks/
cp -r hooks/pre-tool-use-blocker ~/.claude/hooks/

# 2. Make the script executable
chmod +x ~/.claude/hooks/pre-tool-use-blocker/scripts/blocker.py

# 3. That's it — Claude Code auto-detects and calls it
#    before every Bash tool invocation
```

## How it works

Claude Code calls pre-tool-use hooks with a JSON payload on stdin.
The hook inspects the command string against a set of dangerous patterns.
If a match is found, it returns `{ "allow": false }` with a clear message,
and logs the attempt to `~/.claude/hooks/blocked.log`.

## Logs

Every blocked command is timestamped and logged:

```json
{"timestamp": "2026-06-13T12:00:00Z", "tool_name": "Bash", "command": "rm -rf /", "reason": "..."}
```

View logs: `cat ~/.claude/hooks/blocked.log`

## Test

```bash
# Simulate a blocked command:
echo '{"tool_name":"Bash","args":{"command":"rm -rf /"}}' | python3 scripts/blocker.py

# Output: {"allow": false, "message": "..."}

# Simulate a safe command:
echo '{"tool_name":"Bash","args":{"command":"ls -la"}}' | python3 scripts/blocker.py

# Output: {"allow": true}
```

## Safety

The hook **fails open** — if an unexpected error occurs (bad JSON, missing
fields), it allows the command through and logs the error. This ensures the
hook never becomes a denial-of-service vector.

## Files

| File | Purpose |
|------|---------|
| `scripts/blocker.py` | Main hook logic |
| `README.md` | This file |
