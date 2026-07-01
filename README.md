# Claude Builders Bounty Submissions

## Bounty #3: pre-tool-use safety hook

This submission adds a Claude Code `pre-tool-use` hook in `hooks/pre_tool_use_blocker.py` plus tests and installation notes in `hooks/README.md`.

It blocks destructive Bash commands, logs blocked attempts to `~/.claude/hooks/blocked.log`, and exits cleanly for normal commands.
