# Destructive Command Guard

Pre-tool-use hook for Claude Code that blocks dangerous bash commands.

## Install

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre_tool_use.ts https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/destructive-command-guard/pre_tool_use.ts
```

## Blocks
- rm -rf, dd if=, mkfs, fork bombs, chmod -R 777, > /dev/sda
- shutdown, reboot, halt, poweroff
- format, fdisk, parted, mv /*
- DROP TABLE, TRUNCATE, DELETE FROM without WHERE
- git push --force

## Override
Type y at the prompt to confirm execution.