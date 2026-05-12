# Changelog Generator

Generate a structured `CHANGELOG.md` from git history.

## Setup

```bash
chmod +x changelog.sh
```

## Usage

```bash
# Generate CHANGELOG.md from the last tag to HEAD
./changelog.sh

# Specify output file
./changelog.sh --output RELEASE_NOTES.md

# Reverse order (oldest first)
./changelog.sh --reverse

# Target a specific repo
./changelog.sh --repo /path/to/repo

# Verbose mode
./changelog.sh --verbose
```

## How It Works

1. Detects the most recent git tag (or falls back to full history)
2. Collects all commits between that tag and HEAD
3. Auto-categorizes into **Added**, **Fixed**, **Changed**, and **Removed** using conventional commit prefixes
4. Outputs a clean Markdown changelog following [keepachangelog.com](https://keepachangelog.com) conventions
5. Strips conventional-commit prefixes for cleaner bullet text

### Categorization Rules

| Prefix | Category |
|--------|----------|
| `feat`, `add`, `implement`, `introduce`, `create`, `new` | Added |
| `fix`, `bug`, `resolve`, `patch`, `correct`, `hotfix` | Fixed |
| `chore`, `refactor`, `style`, `docs`, `test`, `ci`, `perf`, `build`, `update`, `improve`, `bump` | Changed |
| `remove`, `drop`, `delete`, `deprecate`, `revert` | Removed |
| Everything else | Other |

## Example Output

```markdown
# Changelog

## 0.1.4 (2026-05-12)

### Added
- add --bounty-only flag
- implement reverse sort order

### Fixed
- handle empty GitHub API response
- resolve race condition in concurrent scans

### Changed
- simplify config parsing
- update README

### Removed
- drop deprecated --json-raw flag

---
_47 commits covering v0.1.2..HEAD_
```