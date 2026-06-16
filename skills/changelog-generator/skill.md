# Changelog Generator

Generate a structured, well-formatted CHANGELOG from git history.

## Usage

```
/changelog-generator
```

## What it does

1. Reads git log between the two most recent tags (or last N commits)
2. Categorizes commits into sections: Added, Changed, Fixed, Removed, Security
3. Formats output following Keep a Changelog conventions
4. Saves to CHANGELOG.md (or updates existing)

## Output Format

```markdown
## [version] — YYYY-MM-DD

### Added
- feat: description

### Changed  
- refactor: description

### Fixed
- fix: description

### Removed
- chore: description

### Security
- security: description
```

## Instructions

1. Run `git log --oneline --format="%h %s"` between appropriate refs
2. Parse commit messages by conventional commit prefixes (feat:, fix:, refactor:, docs:, chore:, test:, security:)
3. Group into categories
4. Format each entry as a bullet point with the commit message (without prefix)
5. Prepend version header with current date
6. If CHANGELOG.md exists, prepend new entries after the header; otherwise create new file
7. Co-author each commit with: `Co-Authored-By: Claude <noreply@anthropic.com>`
