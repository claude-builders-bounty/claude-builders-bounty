# Changelog Generator Skill

## Setup (2 steps)

```bash
# 1. Copy the skill
cp SKILL.md ~/.claude/skills/changelog.md
cp changelog.sh ~/.claude/skills/changelog.sh

# 2. Make executable
chmod +x ~/.claude/skills/changelog.sh
```

## Usage

In Claude Code: `/generate-changelog`

Or standalone: `bash changelog.sh`

## Sample Output

```markdown
# Changelog

## [v1.2.0] — 2026-06-05

### Added
- User authentication with JWT tokens
- Dark mode toggle component

### Fixed
- Race condition in checkout flow
- Mobile nav overflow on iOS

### Changed
- Upgraded Next.js to 15.1
- Refactored API routes to use server actions

### Removed
- Legacy cookie-based session handler
```

## Options

| Flag | Description |
|------|-------------|
| `--since <tag>` | Start from a specific git tag |
| `--output <file>` | Write to a custom file path |
