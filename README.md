# Changelog Generator

Generate a structured `CHANGELOG.md` from git history since the last tag.

## Quick Start

```bash
# 1. Copy the script
cp scripts/generate_changelog.py /usr/local/bin/generate-changelog
chmod +x /usr/local/bin/generate-changelog

# 2. Run in any repo
generate-changelog

# 3. Done — CHANGELOG.md is ready
```

## Usage

```
python3 scripts/generate_changelog.py [--output FILE] [--prepend] [--repo-name NAME]
```

| Flag | Description |
|------|-------------|
| `-o, --output` | Output file (default: `CHANGELOG.md`) |
| `-p, --prepend` | Prepend to existing CHANGELOG instead of overwriting |
| `-r, --repo-name` | Repository name (auto-detected) |

## How It Works

1. Finds the latest git tag via `git describe --tags`
2. Collects all commits since that tag
3. Auto-categorizes each commit into **Added** / **Fixed** / **Changed** / **Removed**
4. Outputs a clean `CHANGELOG.md`

## Example Output

```markdown
# Changelog

## [2026-05-14]

### Added
- New user authentication flow (a1b2c3d)
- Dark mode support (e4f5g6h)

### Fixed
- Race condition in database connection pool (i7j8k9l)
- Incorrect timezone conversion (m0n1o2p)

### Changed
- Upgraded dependencies to latest versions (q3r4s5t)

> 5 commits since last tag.
```
