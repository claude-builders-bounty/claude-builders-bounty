# Pre-Tool-Use Hook - Bash Command Blocker

A security hook that intercepts dangerous bash commands before execution.

## Setup
1. Copy `pre-tool-use-hook.sh` to your path.
2. Integrate with Claude Code or shell aliases.
3. Test with `./pre-tool-use-hook.sh rm -rf /` (should block).

## Blocked Patterns
- rm -rf / (and variations)
- dd writes to block devices
- mkfs filesystem creation
- chmod 777 /
- wget/curl piped to shell
- shutdown/reboot
