## Summary of changes
This PR introduces a new Claude Code PreToolUse Bash hook designed to block destructive Bash commands such as `rm -rf`, `DROP TABLE`, force pushes, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause. It logs each blocked attempt to a file and includes a two-command install flow to ensure idempotent setup. The hook also enhances test coverage by adding unit tests for allowed and denied patterns.

## Identified risks
- **Pattern matching accuracy**: Risk of false positives if regex or token parsing fails for complex command strings.
- **Logging reliability**: Dependency on `blocked.log` format; potential issues with timestamps or file permissions.
- **Idempotency assumptions**: Assumes `~/.claude/settings.json` exists and is readable; could fail silently.
- **Command execution flow**: Two-command install may not handle edge cases like missing dependencies.
- **Security**: Logging sensitive project paths or command details without sanitization.

## Improvement suggestions
- Add more granular regex patterns to reduce false positives.
- Validate log file content before writing to avoid corruption.
- Include a dry-run option before blocking.
- Ensure `settings.json` is only modified if the hook is successfully installed.
- Sanitize project paths in log entries to prevent exposure of internal paths.

## Confidence score: High  
The changes address a clear security concern with destructive commands and include robust logging and testing. Minor refinements could further improve reliability.