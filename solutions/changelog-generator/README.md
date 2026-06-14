# Changelog Generator

> Automatically generate a structured `CHANGELOG.md` from your project's git history.

## Quick Start (3 steps)

```bash
# 1. Download the generator
curl -O https://raw.githubusercontent.com/Super-yueyue/changelog-generator/main/generate_changelog.py

# 2. Generate your changelog
python3 generate_changelog.py

# 3. Review the output
cat CHANGELOG.md
```

## Features

- **Auto-categorizes** commits into: `Added` / `Fixed` / `Changed` / `Removed` / `Deprecated` / `Security` / `Performance` / `Documentation`
- **Smart parsing** — understands Conventional Commits (`feat:`, `fix(scope):`, etc.) and falls back to keyword matching
- **Git tag aware** — generates changelog since the last tag by default
- **Commit links** — includes clickable commit hashes when a repo URL is detected
- **Keep a Changelog** format — follows the [popular convention](https://keepachangelog.com)

## Options

| Flag | Description |
|------|-------------|
| `--repo PATH` | Path to git repository (default: `.`) |
| `--output FILE` | Output file (default: `CHANGELOG.md`) |
| `--since REF` | Start from a specific tag/branch (default: last tag) |
| `--version X.Y.Z` | Version number for this release |
| `--repo-url URL` | Repository URL (auto-detected from git remote) |

## Example Output

```markdown
# Changelog

## [1.2.0] - 2026-06-14

### Added
- New user dashboard with real-time analytics (`a1b2c3d`)
- Dark mode support for all pages (`e4f5g6h`)

### Fixed
- Resolved race condition in payment processing (`i7j8k9l`)
- Fixed broken image uploads on Safari (`m0n1o2p`)

### Changed
- Upgraded dependencies to latest versions (`q3r4s5t`)
- Refactored API client for better error handling (`u6v7w8x`)

### Removed
- Deprecated v1 API endpoints (`y9z0a1b`)
```

## How It Works

1. Finds the most recent git tag (or uses all commits if no tags exist)
2. Runs `git log` to collect commits since that tag
3. Categorizes each commit by analyzing its subject line
4. Writes a formatted `CHANGELOG.md` to the specified output path
