# Destructive Command Guard Hook for Claude Code

This hook intercepts and blocks dangerous bash commands (like , , or ) before they are executed by Claude.

## Installation

Run these two commands in your terminal:

```bash
mkdir -p ~/.claude/hooks
curl -sSL https://raw.githubusercontent.com/MichaelSovereign/claude-builders-bounty/main/destructive_guard.py -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Features

- **Intercepts Dangerous Patterns:** Blocks , , , , and more.
- **Audit Logging:** Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with a timestamp and project path.
- **Clear Feedback:** Provides immediate, clear reasons why a command was blocked.

## Configuration

You can add custom patterns to the `DANGEROUS_PATTERNS` list in the script.

