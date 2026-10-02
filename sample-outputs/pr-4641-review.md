## Claude Code PR Review
> PR #4641: feat: /generate-changelog skill + changelog.sh — structured CHANGELOG from git history by @derbaroser-eng
> Backend: Ollama | Confidence: High

### Summary
This PR introduces a robust, automated system for generating structured `CHANGELOG.md` files directly from git history using a new script, `changelog.sh`. The changes include the script itself, detailed documentation in `SKILL.md`, and updates to `README.md` to guide users on how to utilize the new `/generate-changelog` skill. This significantly improves the maintainability and consistency of release notes.

### Risks
- Commit Subject Brittleness:** The categorization rules rely solely on matching prefixes (e.g., `feat*`, `fix*`). If users adopt unconventional commit subject formats that deviate from the defined prefixes, the commits will be incorrectly categorized as "Changed."
- Dependency on `git describe`:** While the script handles the failure of `git describe --tags`, if the repository has tags but they are not standard semantic version tags, the initial tag detection might fail or produce unexpected results, leading to an incorrect changelog range.

### Suggestions
- Improve Error Handling for `git describe`:** Although the script handles the failure of `git describe`, consider adding a more explicit fallback or warning if the initial tag detection fails, guiding the user to manually specify a starting tag if the default behavior is not desired.
- Add Example Commit Subjects:** In `SKILL.md` or the script documentation, provide a small table or list of examples showing how the categorization rules handle edge cases (e.g., "What if a commit starts with `feat` but also contains `fix`?"). This helps users understand the strict nature of the prefix matching.
