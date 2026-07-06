# Safe Command Hook — Claude Code pre-tool-use Hook

Blocks destructive bash commands before they execute in Claude Code.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks
curl -sL -o ~/.claude/hooks/pre-tool-use.py \
  https://raw.githubusercontent.com/dev-nana27/safe-command-hook/main/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py
```

To verify it's active, run in Claude Code:
```
rm -rf /tmp/test
```
You should see: `BLOCKED: rm -rf`

## What It Blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` / `DROP DATABASE` | Destructive DB operations |
| `git push --force` / `git push -f` | Force push overwrites history |
| `TRUNCATE` | Destructive table operation |
| `DELETE FROM` without `WHERE` | Mass data deletion |
| `dd if=... of=...` | Raw device write |

## Logs

Blocked commands are logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## How It Works

Claude Code runs pre-tool-use hooks before every tool call. This hook:
1. Reads the incoming command from stdin (JSON)
2. Checks against blocked patterns
3. Logs and blocks if matched, allows otherwise

## Tested

- Blocks all listed patterns
- Allows normal commands (ls, git commit, npm install, etc.)
- Logs correctly with timestamps
- No interference with everyday development
