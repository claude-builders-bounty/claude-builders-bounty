# Generate Changelog

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

Run the command: `/generate-changelog`

Or run the script directly:
```bash
bash scripts/changelog.sh [OUTPUT_FILE]
```

Default output file is `CHANGELOG.md` in the current directory.

## What it does

1. Fetches commits since the last git tag
2. Auto-categorizes into: Added / Fixed / Changed / Removed
3. Outputs a properly formatted `CHANGELOG.md`

## Categorization Rules

Commits are categorized based on conventional commit prefixes:

| Prefix | Category |
|--------|----------|
| `feat:`, `feature:`, `add:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `change:`, `refactor:`, `update:`, `improve:`, `style:` | Changed |
| `remove:`, `deprecate:`, `delete:` | Removed |
| `docs:`, `chore:`, `test:`, `ci:`, `build:`, `perf:` | Changed (Other) |

Commits without recognized prefixes go into "Other Changes".

## Output Format

```markdown
# Changelog

## [Unreleased]

### Added
- feat: Add user authentication system (#42)
- feat: Implement dark mode toggle (#38)

### Fixed
- fix: Resolve memory leak in cache module (#45)
- fix: Handle null pointer in API response (#41)

### Changed
- refactor: Simplify database connection logic (#39)
- update: Bump dependencies to latest versions (#44)

### Removed
- deprecate: Remove legacy API endpoints (#37)
```

## Setup

1. Clone this skill into your project's `.claude/skills/` directory
2. Copy `scripts/changelog.sh` to your project root
3. Run `bash changelog.sh` to generate

## Requirements

- Git repository with at least one tag
- Bash shell environment
- Git installed and accessible in PATH