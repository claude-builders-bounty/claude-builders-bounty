# Generate Changelog from Git History

## Description
Automatically generate a structured `CHANGELOG.md` from a project's git commit history, categorizing changes into Added/Fixed/Changed/Removed sections.

## Usage
Run `/generate-changelog` in Claude Code, or execute `bash changelog.sh` from the repository root.

## Steps

1. **Fetch commits since last tag**: Run `git log --oneline $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD` to get all commits since the last git tag (or from the beginning if no tags exist).

2. **Categorize commits**: Parse each commit message and classify into categories:
   - **Added**: commits containing "add", "new", "feature", "implement"
   - **Fixed**: commits containing "fix", "bug", "patch", "resolve"
   - **Changed**: commits containing "update", "change", "modify", "refactor", "improve"
   - **Removed**: commits containing "remove", "delete", "drop", "deprecate"
   - **Other**: uncategorized commits go under "Other Changes"

3. **Format output**: Generate a properly formatted `CHANGELOG.md` with:
   - Header: `# Changelog`
   - Version section: `## [Unreleased]` (or use current date)
   - Categorized sections with bullet points
   - Each entry includes the short commit hash and message

4. **Write file**: Save the formatted content to `CHANGELOG.md` in the repository root.

5. **Verify**: Confirm the file was created and contains entries for each category that has commits.

## Example Output
```markdown
# Changelog

## [2026-09-25]

### Added
- c6ea084 implement: complete WP1-WP9 remediation + Human Network records

### Fixed
- 33d69e8 fix: skip catalog-toolkit PDF/DOCX tests gracefully

### Changed
- 0a54c51 canonical: update submodule pointers to stable snapshots

### Removed
- e0e59dfb correct: recover expert_judgment.py into legacy donor archive
```

## Notes
- If no tags exist, fetches all commits from repository inception
- Commit messages are case-insensitive for category matching
- Duplicate commits are not filtered (git log handles this)
- The script exits with code 0 on success, non-zero on failure
