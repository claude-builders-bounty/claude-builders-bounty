# Claude Code Security Hook

A lightweight, robust `pre-tool-use` hook for Claude Code that prevents the AI from executing destructive bash or SQL commands. 

## Features
- Blocks highly destructive operations: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` (without a `WHERE` clause).
- Silently allows normal, safe operations to pass.
- Maintains an audit trail by logging all blocked attempts to `~/.claude/hooks/blocked.log` (with timestamp, command, and project path).
- Returns a clear, human-readable error message to Claude so it understands *why* the action was blocked.

## Installation

You can install this hook in just two commands:

```bash
mkdir -p ~/.claude/hooks
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/claude-security-hook/main/pre_tool_use.py -o ~/.claude/hooks/pre_tool_use && chmod +x ~/.claude/hooks/pre_tool_use
```

## How it works
Claude Code executes hooks by passing tool payloads via `stdin` in JSON format. This script intercepts any payload destined for terminal/bash execution tools, parses the command string, and applies regex pattern matching to stop destructive actions before they are even sent to the system shell.

*Built for the Opire $100 Bounty Challenge.*
