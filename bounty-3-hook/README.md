# Destructive Command Blocker — Claude Code Hook

Blocks dangerous bash commands (rm -rf /, sudo, drop table, etc.) before they execute.

## Installation
```bash
# In your project root
mkdir -p .claude/hooks/pre-tool-use/
cp block-destructive.sh .claude/hooks/pre-tool-use/block.sh
# or use Python version:
cp block_destructive.py .claude/hooks/pre-tool-use/block.py
```

## How it works
- Reads the bash command from stdin
- Checks against known destructive patterns
- Returns `{"allowed": false}` with a reason if blocked
- Returns `{"allowed": true}` if safe

## Detection coverage
- Filesystem destruction: rm -rf /, dd, mkfs
- Permission abuse: chmod -R 777, chown -R
- Git force operations: push --force, reset --hard
- Database destruction: drop table, drop database, truncate
- System escalation: sudo, fork bombs
- Remote execution: wget/curl piped to shell
