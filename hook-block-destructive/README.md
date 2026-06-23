# Destructive Command Blocker Hook

Pre-tool-use hook for Claude Code that blocks dangerous bash commands.

## Install (2 commands)

`ash
mkdir -p ~/.claude/hooks
cp pre_tool_use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use.py
`

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| m -rf | Force/recursive delete |
| DROP TABLE | Database table destruction |
| git push --force | Force push overwrite |
| DELETE FROM (no WHERE) | Full table deletion |
| TRUNCATE TABLE | Table truncation |
| git reset --hard | Irreversible reset |
| chmod 777 | World-writable permissions |
| Raw disk writes | Hardware destruction |

## Override

Set env var to bypass temporarily:
`ash
CLAUDE_ALLOW_DESTRUCTIVE=1
`

## Logs

All blocked attempts logged to ~/.claude/hooks/blocked.log with timestamp, reason, and project path.