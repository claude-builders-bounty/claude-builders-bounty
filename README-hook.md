# Pre-Tool-Use Hook for Claude Code

Blocks destructive bash commands before they are executed.

## Install (2 commands)
\\ash
# 1. Copy hook script
cp pre-tool-use-hook.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py

# 2. Create hooks directory if needed
mkdir -p ~/.claude/hooks
\
## Blocked Commands
- m -rf\ / m -fr- \DROP TABLE- \TRUNCATE TABLE- \DELETE FROM\ without WHERE
- \git push --force\ / \git push -f- \ormat\ on disk devices
- \dd if=... of=/dev/...- \sh -c rm -rf
## How It Works
Claude Code calls this hook before executing any bash tool.
If the command matches a blocked pattern, the hook returns exit code 1
and prints a clear message explaining why it was blocked.

All blocked attempts are logged to \~/.claude/hooks/blocked.log\.

## Log Format
\[2026-09-21T15:30:00] BLOCKED: rm -rf /tmp/test | Project: /home/user/project
\
## Unblocking
To allow a specific command, edit \pre-tool-use-hook.py\ and remove
the matching pattern from \BLOCKED_PATTERNS\.
