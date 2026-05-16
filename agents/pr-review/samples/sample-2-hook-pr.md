## 🔍 PR Review: feat: pre-tool-use hook blocking destructive bash commands

### 📋 Summary
This PR implements a Claude Code PreToolUse hook that intercepts bash commands before execution and blocks dangerous patterns like `rm -rf /`, `DROP TABLE`, `git push --force`, and filesystem-level destructive operations. It includes an installer script and 16 unit tests.

### ⚠️ Identified Risks
- Regex-based command detection can be bypassed with obfuscation (e.g., `r\m -rf /`, variable expansion `$CMD`, or base64-encoded commands piped to bash)
- The hook only checks the `tool_input.command` field — if Claude uses a different input schema in future versions, the hook would silently pass all commands
- Logging to `~/.claude/hooks/blocked.log` without log rotation could grow unbounded on active systems

### 💡 Improvement Suggestions
- Add a configurable allowlist/denylist so users can customize blocked patterns
- Implement log rotation or max file size check (e.g., truncate after 1MB)
- Add a `--strict` mode that also blocks commands with pipes to `bash`, `sh`, or `eval`
- Consider normalizing commands (lowercase, expand aliases) before pattern matching

### 🎯 Confidence Score
**Medium** — The implementation is solid for common cases and the test coverage is good. However, regex-based security controls are inherently bypassable by determined users, which limits the hook to a "safety net" rather than a security boundary.

---
*Reviewed by claude-review v1.0.0*
