## 🤖 Claude Code Review — claude-builders-bounty/claude-builders-bounty#655

## Summary
This PR adds a Python `PreToolUse` hook for Claude Code that intercepts potentially destructive bash commands before execution. The hook reads tool input JSON from stdin, pattern-matches the `command` field against a blocklist of dangerous patterns, logs blocked attempts with timestamps to `~/.claude/hooks/blocked.log`, and returns a structured `{"decision": "block", "reason": "..."}` response to prevent execution.

## Risks
- **False positives on string content**: The regex patterns match anywhere in the command string, so a command like `echo "rm -rf reminder"` would be incorrectly blocked since it contains the pattern in a safe context
- **No bypass mechanism**: Legitimate uses of force-push (e.g., after an interactive rebase) are completely blocked with no way for the user to authorize the action
- **Log file grows unbounded**: Blocked attempts are appended without log rotation — long-running instances could accumulate large log files
- **Python process per invocation**: Spawning a Python subprocess for every Bash tool call adds latency to all commands, not just blocked ones

## Suggestions
- Add word-boundary awareness to reduce false positives — check for the pattern at the start of the command or after `&&`/`|` pipe characters
- Implement an allowlist mechanism (e.g., `# claude-ok` comment in the command) for authorized overrides
- Add log rotation using Python's `logging.handlers.RotatingFileHandler`
- Provide a `--test` flag to validate hook behavior without installing it system-wide
- Consider caching the Python interpreter startup with a persistent daemon socket to reduce per-call overhead

## Confidence
**Level:** High
**Reasoning:** The implementation is straightforward and correct for the specified patterns; the risks identified are real but manageable, and the hook correctly handles the Claude Code hook protocol.
