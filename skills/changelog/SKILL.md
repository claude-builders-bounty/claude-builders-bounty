# Skill: Generate CHANGELOG from Git History

## Description
Automatically generates a structured `CHANGELOG.md` from a project's git commit history.

## Usage

### Option 1: Claude Code Skill
Run `/generate-changelog` in Claude Code.

### Option 2: Bash Script
```bash
bash skills/changelog/changelog.sh
```

## How It Works

1. Fetches commits since the last git tag (or all commits if no tags exist)
2. Analyzes commit messages using Conventional Commits pattern
3. Categorizes into: Added, Fixed, Changed, Removed
4. Generates a formatted `CHANGELOG.md`

## Acceptance Criteria
- ✅ Works via `/generate-changelog` command or `bash changelog.sh`
- ✅ Fetches commits since the last git tag
- ✅ Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- ✅ Outputs a properly formatted `CHANGELOG.md`
- ✅ Includes a sample output in the PR
- ✅ README with setup instructions in 3 steps or fewer

## Commit Message Format

This skill recognizes Conventional Commits:
- `feat:`, `feature:` → Added
- `fix:`, `bugfix:` → Fixed
- `refactor:`, `chore:`, `docs:`, `style:`, `test:` → Changed
- `remove:`, `delete:` → Removed

## Sample Output

```markdown
# Changelog

## [1.2.0] - 2024-03-27

### Added
- User authentication system
- Dashboard analytics page
- API rate limiting

### Fixed
- Login redirect loop
- Database connection timeout

### Changed
- Updated dependencies to latest versions
- Improved error handling messages

### Removed
- Deprecated legacy API endpoints
```

## Setup (3 steps)

1. Copy `skills/changelog/changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run: `bash changelog.sh`

## Files
- `SKILL.md` - This documentation
- `changelog.sh` - The bash script
- `sample-output.md` - Example CHANGELOG.md output