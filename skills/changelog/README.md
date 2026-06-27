# CHANGELOG Generator Skill

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from your git commit history.

## Features

- Automatically categorizes commits into Added, Fixed, Changed, Removed
- Recognizes Conventional Commits format
- Works with or without git tags
- Generates clean, readable changelogs

## Setup (3 Steps)

### Step 1: Copy the script
```bash
cp skills/changelog/changelog.sh /path/to/your/project/
```

### Step 2: Make it executable
```bash
chmod +x changelog.sh
```

### Step 3: Run it
```bash
bash changelog.sh
```

## Usage

### As a Claude Code Skill
In Claude Code, simply run:
```
/generate-changelog
```

### As a Bash Script
```bash
bash changelog.sh
```

## Commit Message Format

This tool recognizes [Conventional Commits](https://www.conventionalcommits.org/):

| Commit Type | Category |
|-------------|----------|
| `feat:`, `feature:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `refactor:`, `chore:`, `docs:`, `style:`, `test:` | Changed |
| `remove:`, `delete:` | Removed |

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2024-03-27

### Added
- feat(auth): implement JWT token refresh mechanism
- feat(dashboard): add real-time analytics widgets
- feat(api): add rate limiting middleware

### Changed
- refactor(core): improve error handling patterns
- chore(deps): update dependencies to latest versions

### Fixed
- fix(auth): resolve login redirect loop issue
- fix(db): handle connection timeout gracefully

### Removed
- remove(legacy): deprecate v1 API endpoints
```

## Requirements

- Git installed and configured
- Bash shell
- Repository must have at least one commit

## License

MIT