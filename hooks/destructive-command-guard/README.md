# Destructive Command Guard

Quick install (2 commands):

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre_tool_use.ts https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/destructive-command-guard/pre_tool_use.ts
```

Blocks: rm -rf, dd, mkfs, fork bombs, chmod 777, disk writes, shutdown/reboot, DROP TABLE, git push --force.

Logs to `~/.claude/hooks/blocked.log`