## PR Review

### Summary
This PR adds a pre-tool-use hook for Claude Code that blocks dangerous bash commands. It implements five pattern-matching rules (rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE) and logs blocked attempts to a local file. The implementation is clean and follows the project's conventions.

### Identified Risks
- The regex patterns use simple string matching which could produce false positives (e.g., comment references to `rm -rf` would be blocked)
- No test coverage is included in the PR
- The hook requires manual installation (cp to ~/.claude/hooks/) which could be automated

### Improvement Suggestions
- Consider adding test cases for edge cases (commented-out patterns, multi-line commands)
- Add an allowlist mechanism for safe-but-matching commands
- Include a one-line install command in the README

### Confidence Score
**Confidence: High**

### Files Changed (with line counts)
- pre-tool-use (+98/-0)
- README.md (+52/-0)

### Key Observations
- Well-structured Python script with clear pattern definitions
- Good logging with timestamps and project context
- README is clear and provides install/uninstall instructions
