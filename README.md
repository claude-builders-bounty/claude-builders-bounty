# Claude Code Safety Hook

Pre-tool-use hook that intercepts dangerous bash commands before execution.

## Setup
1. Copy `hooks/pre-tool-use.py` to `~/.claude/hooks/pre-tool-use`
2. Make executable: `chmod +x ~/.claude/hooks/pre-tool-use`
3. Claude Code auto-detects and runs the hook on every Bash tool call

## Blocked Patterns
- `rm -rf` — destructive delete
- `DROP TABLE` / `DROP DATABASE` — SQL destruction
- `git push --force` — force push
- `DELETE FROM table` without WHERE — full table deletion
- Raw disk writes (`/dev/sd*`)
- `curl | sh` / `wget | sh` — pipe to shell
- `chmod -R 777` — world-writable

## Logs
Blocked attempts written to `~/.claude/hooks/blocked.log` in JSON format.
