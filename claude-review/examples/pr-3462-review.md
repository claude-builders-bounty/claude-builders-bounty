### Summary
This PR adds a changelog generator skill (SKILL.md) and a companion bash script that auto-generates CHANGELOG.md from git history since the last tag using conventional commit prefixes. It follows the Keep a Changelog format with Added/Fixed/Changed/Removed categories.

### Identified Risks
- The script writes to CHANGELOG.md without checking if one already exists, potentially overwriting manual changes
- The commit categorization logic is fragile — it parses commit subjects but doesn't handle multi-line commits or non-conventional prefixes
- No `.git` directory check — will fail silently in non-git directories

### Improvement Suggestions
1. **Backup existing CHANGELOG.md** — rename existing file before overwriting, or append instead
2. **Add proper conventional commit parsing** — use `git log --format="%s%n%b"` to capture full commit message body
3. **Add error handling** — check `git rev-list` return code, handle repos with no commits

### Confidence Score
**Medium** — The core logic is straightforward and correct, but there are several edge cases around git history parsing that could cause issues.
