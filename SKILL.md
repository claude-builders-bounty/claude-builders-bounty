---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
version: 1.0.0
---

# Generate Changelog Skill

Generates a categorized CHANGELOG.md from git commits since the last tag.

## Usage

```bash
/skill generate-changelog
# or
bash changelog.sh [output_file]
```

## Categories

Commits are auto-categorized by conventional commit prefixes:
- `feat:` → **Added**
- `fix:` → **Fixed**
- `refactor:`, `style:`, `perf:` → **Changed**
- `revert:`, `remove:`, `delete:` → **Removed**
- Other → **Changed**

## Output Format

```markdown
# Changelog

## [Unreleased] - YYYY-MM-DD

### Added
- Description of new feature (abc1234)

### Fixed
- Bug fix description (def5678)
```
