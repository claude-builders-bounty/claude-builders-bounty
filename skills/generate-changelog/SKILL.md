# Generate Changelog

> A Claude Code skill that generates a structured `CHANGELOG.md` from your
> project's git history.

## Description

This skill scans commits since the last git tag, auto-categorizes them into
**Added** / **Fixed** / **Changed** / **Removed**, and writes a clean
`CHANGELOG.md` to your project root.

## Usage

### Via Claude Code command
```
/generate-changelog
```

### Via shell (standalone)
```bash
# Inside your project repo:
bash .claude/skills/generate-changelog/scripts/changelog.sh

# Custom output file:
bash .claude/skills/generate-changelog/scripts/changelog.sh --output CHANGES.md

# Specify a tag boundary:
bash .claude/skills/generate-changelog/scripts/changelog.sh --tag v2.0.0
```

### As a hook (auto-generate on release)
Add to your release workflow:
```yaml
- name: Generate Changelog
  run: bash .claude/skills/generate-changelog/scripts/changelog.sh
```

## How it works

1. Finds the most recent git tag (`git describe --tags --abbrev=0`).
2. Collects all non-merge commits since that tag.
3. Parses commit messages for conventional commit prefixes:
   - `feat:`, `feature:`, `add:`, `implement:` → **Added**
   - `fix:`, `bugfix:`, `patch:`, `hotfix:` → **Fixed**
   - `remove:`, `delete:`, `drop:`, `deprecate:` → **Removed**
   - Everything else → **Changed**
4. Writes a formatted `CHANGELOG.md` to the project root.

## Requirements

- Git repository with commits
- Bash (Linux, macOS, or WSL/Git Bash on Windows)

## Files

| File | Purpose |
|------|---------|
| `scripts/changelog.sh` | The changelog generator script |
| `SKILL.md` | This skill definition |

## Example output

```markdown
# Changelog

## v1.5.0 (2026-06-13)

### Added
- User authentication via OAuth2
- Dark mode toggle in settings

### Changed
- Upgraded axios from 1.6 to 1.7
- Refactored database layer for better performance

### Fixed
- Login redirect loop on expired sessions
- Missing error handling in payment gateway

### Removed
- Deprecated v1 API endpoints
```
