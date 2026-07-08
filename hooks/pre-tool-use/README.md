# Claude Code Hook: Block Destructive Bash Commands

This is a `pre-tool-use` hook for Claude Code that prevents the agent from executing destructive bash or SQL commands. It intercepts commands before execution, blocking patterns like `rm -rf`, `DROP TABLE`, or `git push --force`.

## Features
- **Blocks** `rm -rf`, `DROP TABLE`, `TRUNCATE`, `DELETE FROM` (without WHERE), and `git push --force`
- **Logs** all blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.
- **Explains** directly to Claude why the action was blocked.
- **Cross-platform** Python implementation, transparent to normal bash commands.

## Installation

You can install this hook in 2 commands:

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use
```

*(Note: Replace the URL above with the actual raw file URL if necessary once merged).*

If you already downloaded this repository, simply run from this directory:
```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Requirements
- Python 3+ must be installed on your system.
