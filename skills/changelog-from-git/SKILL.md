# SKILL.md — Generate CHANGELOG from Git History

Generate a structured `CHANGELOG.md` from your project's git history — automatically categorizing commits into `Added`, `Fixed`, `Changed`, and `Removed`.

## Usage

```
/generate-changelog
```

Or run directly:

```bash
bash skills/changelog-from-git/changelog.sh
```

## How It Works

1. Fetches all commits since the last git tag (or from the beginning if no tags exist)
2. Groups commits by conventional commit prefix:
   - `feat:` / `feat(scope):` → **Added**
   - `fix:` / `fix(scope):` → **Fixed**
   - `chore:` / `refactor:` / `perf:` → **Changed**
   - `BREAKING CHANGE:` → **Removed** (with BREAKING NOTICE)
3. Outputs a properly formatted `CHANGELOG.md`

## Requirements

- `git` CLI
- `grep`, `sed`, `awk` (standard Unix tools — available on Linux/macOS/WSL/Git Bash)

No external dependencies. No API keys needed.

## Output Format

```markdown
# Changelog

## [Unreleased]

### Added
- Feature description (@username, #123)

### Fixed
- Bug fix description (@username, #456)

### Changed
- Refactor or improvement (@username, #789)

### Removed
- Breaking change notice
```

## Testing

Tested on: `claude-builders-bounty` repository — see `sample-output.md` in this directory.
