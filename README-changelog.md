# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from git history. Works as a standalone bash script or as a Claude Code skill (`/generate-changelog`).

## Usage (3 steps)

```bash
# 1. Make executable
chmod +x changelog.sh

# 2. Run in any git repo
./changelog.sh /path/to/your/repo

# 3. Or run in current directory
./changelog.sh
```

## Output

Generates `CHANGELOG.md` with auto-categorized sections:

- **Added** -- new features (commits starting with `add`, `feat`, `new`, `implement`, `create`, `introduce`)
- **Fixed** -- bug fixes (commits starting with `fix`, `bug`, `patch`, `resolve`, `correct`, `repair`)
- **Changed** -- everything else (refactors, updates, docs, etc.)
- **Removed** -- deletions (commits starting with `remove`, `delete`, `drop`, `deprecate`)

## How It Works

1. Finds the latest git tag (or falls back to the first commit)
2. Collects all commits since that tag
3. Categorizes by conventional commit prefix matching
4. Outputs formatted `CHANGELOG.md`

## As a Claude Code Skill

Create `SKILL.md` in your project's `.claude/skills/changelog/`:

```markdown
# Generate Changelog

Run `./changelog.sh` to generate a structured CHANGELOG.md from the git history since the last tag.

Usage: `/generate-changelog`
```

## Example Output

```markdown
# Changelog

## [v1.2.0] - 2026-05-05

### Added
- feat: Add user authentication system
- Add dark mode toggle

### Fixed
- fix: Resolve login redirect loop
- patch: Fix memory leak in worker pool

### Changed
- refactor: Simplify API response format
- Update dependency versions

### Removed
- remove: Drop deprecated v1 endpoint
```
