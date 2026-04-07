# Pre-tool-use Hook
> Last updated: 2026-04-07
## Overview
The pre-tool-use hook is designed to intercept and block execution of dangerous bash commands, preventing accidental data loss or corruption. This feature was implemented to enhance user safety when using command-line tools.
## How It Works
The hook script located at `~/.claude/hooks/pre-tool-use-hook.sh` checks the command input against a list of predefined destructive patterns. If a match is found, the command is blocked, and an entry is logged in `~/.claude/hooks/blocked.log`. The user receives a message explaining the block.
## Configuration
No configuration required.
## Usage
To install the hook, run the following commands:
```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use-hook.sh https://<raw-link-to-your-script>
chmod +x ~/.claude/hooks/pre-tool-use-hook.sh
```
## References
- Closes issue #3