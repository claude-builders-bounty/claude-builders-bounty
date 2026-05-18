# Changelog Generator

Generate structured `CHANGELOG.md` files from git history. Supports conventional commits and freeform messages.

## Setup (3 steps)

```bash
# 1. Save changelog.sh to your project
curl -O https://raw.githubusercontent.com/vanhci/claude-builders-bounty/main/changelog.sh
chmod +x changelog.sh

# 2. Run from your repo
cd /path/to/your/project
bash changelog.sh

# 3. Done — your CHANGELOG.md is ready
cat CHANGELOG.md
```

## Options

| Flag | Description |
|------|-------------|
| `--since-tag <tag>` | Start changelog from a specific tag |
| `--repo <path>` | Target repository (default: current dir) |
| `--output <file>` | Output file (default: `CHANGELOG.md`) |

## Examples

```bash
# From last release tag
bash changelog.sh --repo .

# From a specific version
bash changelog.sh --since-tag v2.0.0 --output HISTORY.md

# From any git repository
bash changelog.sh --repo /path/to/project
```

## Requirements

- `git`
- `python3`

## Output Format

Commits are automatically categorized into sections:
- **Added** — new features
- **Fixed** — bug fixes
- **Changed** — improvements, refactors, dependency updates
- **Removed** — deletions
- **Security** — security-related changes

Uses [Keep a Changelog](https://keepachangelog.com/) format.

## Sample Output

```markdown
# Changelog

## [2026-05-18]
### Added
- user authentication module (a1b2c3d)

### Fixed
- session timeout edge case (e5f6g7h)

### Changed
- upgrade async HTTP client (i9j0k1l)
```
