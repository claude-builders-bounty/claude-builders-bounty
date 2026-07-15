# Generate CHANGELOG from Git History

**Description**: Automatically generate a structured CHANGELOG.md from a project's git history, categorizing commits since the last tag.

**Trigger**: `/generate-changelog`

**Usage**:
1. Run `/generate-changelog` in any git repository
2. The tool fetches commits since the last git tag (or all commits if no tags exist)
3. Auto-categorizes commits into: Added / Changed / Fixed / Removed
4. Outputs a well-formatted CHANGELOG.md

---

## Instructions

When the user triggers this skill:

1. **Detect the environment**: Check if we're in a git repository
2. **Find the last tag**: Run `git describe --tags --abbrev=0` to get the latest tag
3. **Fetch commits**: Get all commits since that tag (or all history if no tags)
4. **Categorize**: For each commit, analyze the message and assign to a category:
   - **Added**: feat, add, create, new, implement, introduce
   - **Changed**: change, update, modify, refactor, improve, enhance, chore
   - **Fixed**: fix, bug, patch, resolve, correct, repair
   - **Removed**: remove, delete, drop, deprecate, clean
5. **Generate markdown**: Output properly formatted CHANGELOG.md
6. **Save**: Write to CHANGELOG.md in the repo root

## Commit Categorization Rules

- If message starts with conventional commit prefix (feat:, fix:, chore:, etc.), use that
- Otherwise, match keywords in the message (case-insensitive)
- Default to "Changed" if no match found

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- [message] ([short_hash]) - [date]

### Changed
- [message] ([short_hash]) - [date]

### Fixed
- [message] ([short_hash]) - [date]

### Removed
- [message] ([short_hash]) - [date]
```
