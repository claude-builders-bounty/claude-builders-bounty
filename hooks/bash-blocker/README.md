# Claude Code Bash Blocker Hook

A `pre-tool-use` hook for Claude Code that automatically intercepts and blocks dangerous commands (e.g., `rm -rf`, `DROP TABLE`, `git push --force`) from being executed by the AI, keeping your system safe.

## Installation
Install this hook directly into your Claude Code hooks directory in just two commands:

```bash
mkdir -p ~/.claude/hooks
curl -sL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/bash-blocker/pre-tool-use.py -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
