## 🔍 PR Review: feat: add changelog generator from git history

### 📋 Summary
This PR adds a changelog generator tool that parses git log output and produces a structured CHANGELOG.md file. It includes both a bash script for quick usage and a Python script for more advanced filtering, along with a SKILL.md for Claude Code integration.

### ⚠️ Identified Risks
- The bash script uses `git log --pretty=format` without sanitizing commit messages, which could break Markdown formatting if commits contain special characters like `|` or `#`
- No input validation on the date range parameters — malformed dates will produce silent failures
- The Python script shells out to `git log` without escaping arguments, potential command injection if used programmatically with untrusted input

### 💡 Improvement Suggestions
- Add input validation for date parameters (ISO 8601 format check)
- Escape special Markdown characters in commit messages before writing
- Add a `--dry-run` flag to preview output without writing files
- Consider adding conventional commit parsing (feat/fix/chore grouping)

### 🎯 Confidence Score
**High** — The code is straightforward, well-documented, and the scope is limited. The risks identified are edge cases rather than fundamental design issues.

---
*Reviewed by claude-review v1.0.0*
