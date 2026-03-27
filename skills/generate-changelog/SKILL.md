# Generate Changelog

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

Run the bash script:

```bash
bash changelog.sh
```

Or invoke via Claude Code: `/generate-changelog`

## What It Does

- Fetches commits since the last git tag (or all commits if no tag exists)
- Auto-categorizes commits into: **Added** / **Fixed** / **Changed** / **Removed**
- Outputs a properly formatted `CHANGELOG.md` in the project root

## Commit Convention

For best results, use conventional commit prefixes:

- `add:` / `feat:` / `new:` → **Added**
- `fix:` / `bug:` / `bugfix:` → **Fixed**
- `change:` / `update:` / `refactor:` / `chore:` → **Changed**
- `remove:` / `delete:` / `drop:` → **Removed**
- Commits without a matching prefix go into **Changed** by default

## Output Format

```markdown
# Changelog

## [Unreleased]

### Added
- feature: description of new feature

### Fixed
- fix: description of bug fix

### Changed
- refactor: description of change

### Removed
- remove: description of removal
```

## Requirements

- Git repository with commit history
- Bash 4+
