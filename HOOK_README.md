# Claude Code Safety Hook — `$100`

A **pre-tool-use** hook for Claude Code that intercepts dangerous bash commands before they execute.

## Blocked Commands

| Pattern | Description |
|---------|-------------|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Database table destruction |
| `git push --force` | Force push to remote |
| `TRUNCATE` | Table data deletion |
| `DELETE FROM ...` (no WHERE) | Full table wipe |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Install (2 commands)

```bash
# Python (recommended):
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/bgagosmohan/claude-builders-bounty/main/pre-tool-use-hook.py -o ~/.claude/hooks/pre_tool_use && chmod +x ~/.claude/hooks/pre_tool_use

# Bash (zero-dependency):
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/bgagosmohan/claude-builders-bounty/main/pre-tool-use-hook.sh -o ~/.claude/hooks/pre_tool_use && chmod +x ~/.claude/hooks/pre_tool_use
```

## Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | ~/.claude/hooks/pre_tool_use
# → {"continue":false,"reason":"🚫 BLOCKED — rm -rf (recursive force delete)..."}

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | ~/.claude/hooks/pre_tool_use
# → {"continue":true}
```

## Log Format

```
[2026-05-17T09:30:00] reason=rm -rf (recursive force delete) project=/home/user/myapp command="rm -rf /tmp/*"
```

## Uninstall

```bash
rm ~/.claude/hooks/pre_tool_use
```
