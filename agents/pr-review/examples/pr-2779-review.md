## 🤖 Claude Review: [BOUNTY $50] SKILL: Generate structured CHANGELOG from git history

### Summary
This PR adds `scripts/changelog.sh`, a bash script that generates a structured `CHANGELOG.md` from git history. It fetches commits since the last tag, categorizes them into Added/Fixed/Changed/Removed, and outputs markdown. A README with setup instructions is also included.

### Identified Risks
- **risk: No input sanitization on `--repo` path** — The `--repo` argument is passed directly to `git -C "$REPO_DIR"`. A user could pass an unexpected path or command injection via the argument. Realistically the risk is low (CLI tool, local use), but adding basic path validation (e.g., rejecting non-existent directories) would harden it.
- **risk: No `git log` error handling** — If the repo has no commits or the tag range is invalid, `git log` will fail silently or produce unexpected output. The script should check `$?` after git commands and exit with a clear message.

### Improvement Suggestions
- **suggestion: Add `set -e` earlier** — `set -euo pipefail` is present but could be reinforced with explicit error handling on `git describe --tags` (which fails on repos with no tags). Consider `tag=$(git describe --tags --abbrev=0 2>/dev/null || true)` to handle no-tag repos gracefully.
- **suggestion: Handle empty commit ranges** — If no commits exist in the range, the script currently produces an empty CHANGELOG. A `No new commits since last release` placeholder would be more informative.
- **suggestion: Support `--help` flag** — Currently only `--repo`, `--output`, and `--since` are documented. Adding `--help` improves UX.

### Confidence Score
**High** — The implementation is straightforward, the acceptance criteria are fully met, and the code is clean. The risks above are minor edge cases, not structural issues.
