# Claude Code Security Hook

A `pre-tool-use` hook for Claude Code that automatically blocks destructive bash commands before they are executed. 

This hook intercepts bash execution and looks for dangerous patterns like `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and unbounded `DELETE FROM` statements. It prevents them from running and logs the attempt.

## Installation

Install the hook in just two commands:

```bash
mkdir -p ~/.claude/hooks
curl -sL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pre-tool-use -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Features

- **Intercepts Destructive Commands:** Checks all `bash` and `run_command` tool uses.
- **Blocks Dangerous Patterns:** Stops `rm -rf`, `git push --force`, `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` (if it lacks a `WHERE` clause).
- **Audit Logging:** Automatically logs all blocked attempts (with timestamp, attempted command, and project path) to `~/.claude/hooks/blocked.log`.
- **Seamless:** Allows all regular, safe commands to pass through without interference.
- **Claude Feedback:** Returns a clear, explanatory message to Claude Code when an action is blocked.
