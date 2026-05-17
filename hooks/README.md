# Claude Code Pre-Tool-Use Hook

A safety hook for Claude Code that intercepts dangerous bash commands.

## Installation

\\\ash
mkdir -p ~/.claude/hooks
# Copy pre_tool_use_hook.py to this location
chmod +x ~/.claude/hooks/pre_tool_use_hook.py
\\\

## What It Blocks

- rm -rf, DROP TABLE, DROP DATABASE, TRUNCATE
- git push --force
- DELETE FROM without WHERE
- shred, mkfs, fdisk

## Testing

\\\ash
echo '{\"tool_name\":\"bash\",\"tool_input\":{\"command\":\"rm -rf /\"}}' | python3 ~/.claude/hooks/pre_tool_use_hook.py
# Returns: {\"action\":\"block\",\"message\":\"Blocked...\"}
\\\

## Bounty

Created for: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3