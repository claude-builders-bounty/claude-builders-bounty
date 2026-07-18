### Summary
This PR adds a pre-tool-use hook that intercepts bash commands before execution and blocks destructive operations like `rm -rf`, `DROP TABLE`, `git push --force`, and `DELETE FROM` without `WHERE`. Blocked attempts are logged with timestamps for audit.

### Identified Risks
- The regex `DELETE FROM` detection without `WHERE` can be bypassed with `\n` or SQL comments like `DELETE /*x*/ FROM`
- The logger appends indefinitely with no rotation or size limit
- The hook blocks based on string matching rather than AST parsing, so `rm -$flags rf` or `rm --recursive --force` could bypass

### Improvement Suggestions
1. **Add log rotation** — cap the log at 1MB with automatic truncation
2. **Use tokenization for detection** — normalize whitespace and strip SQL comments before pattern matching
3. **Add an allowlist** — allow certain paths/projects to use destructive commands via a config file

### Confidence Score
**High** — The hook correctly intercepts and blocks the most common destructive patterns with proper logging. Edge case bypasses exist but require intentional effort.
