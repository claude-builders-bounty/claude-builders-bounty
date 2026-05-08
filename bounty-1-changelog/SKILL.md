# Skill: Generate CHANGELOG

## Description
Generate a structured CHANGELOG.md from git history, categorizing commits by conventional-commit type into Keep-a-Changelog sections.

## Command
`/generate-changelog`

## Instructions

When the user runs `/generate-changelog`, follow these steps:

### 1. Gather Git History
```bash
# Get all tags sorted by version
git tag --sort=version:refname

# Get commits since last tag (for unreleased)
git log --no-merges --format="%H %s" <last-tag>..HEAD

# Get commits between two tags
git log --no-merges --format="%H %s" v1.0.0..v1.1.0
```

### 2. Categorize Each Commit

Map conventional-commit prefixes to categories:

| Prefix | Category |
|--------|----------|
| `feat:` | **Added** |
| `fix:` | **Fixed** |
| `refactor:`, `perf:`, `docs:`, `style:`, `test:`, `chore:`, `ci:`, `build:` | **Changed** |
| `remove:` | **Removed** |
| `deprecate:` | **Deprecated** |
| `feat!:` or `fix!:` or `BREAKING CHANGE` footer | **Removed** |

### 3. Generate CHANGELOG.md

Use this format:
```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- description (abc1234)

### Fixed
- description (def5678)

## [1.2.0] - 2024-01-15

### Added
- **scope:** description (abc1234)

### Changed
- description (def5678)

### Removed
- description (ghi9012)
```

### 4. Rules
- Group by version tag, newest first
- Include an `[Unreleased]` section for commits after the last tag
- Strip the type prefix from commit messages in the output
- Include the short hash (7 chars) in parentheses after each entry
- Include scope in bold if present: `**auth:** added OAuth support`
- Skip merge commits
- Skip empty or whitespace-only messages
- If no tags exist, treat entire history as `[Unreleased]`

### 5. Output
Write the result to `CHANGELOG.md` in the project root. Confirm to the user with a summary of how many entries were generated.
