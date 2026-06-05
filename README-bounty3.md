# Pre-Tool-Use Hook

Blocks destructive commands before execution in Claude Code.

## Install
`ash
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
`

## Blocks
- rm -rf, rm -fr, rm --recursive
- DROP TABLE, DROP DATABASE, TRUNCATE TABLE
- git push --force, git push -f
- DELETE FROM without WHERE
- shutdown, dd, mkfs, chmod 777

All blocked attempts logged to ~/.claude/hooks/blocked.log
