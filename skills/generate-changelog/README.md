# generate-changelog

A bash script + Claude Code skill that generates a structured `CHANGELOG.md` from git history.

## Features

- Fetches commits since the last git tag
- Auto-categorizes into: **Added** / **Fixed** / **Changed** / **Removed** / **Documentation** / **Maintenance**
- Supports conventional commit format (`feat:`, `fix:`, `refactor:`, etc.)
- Generates commit links to GitHub
- Zero dependencies — pure bash

## Installation (2 steps)

```bash
# 1. Copy the script to your project
cp changelog.sh /path/to/your/project/

# 2. Run it anytime
cd /path/to/your/project && bash changelog.sh
```

## Usage

```bash
# Generate CHANGELOG.md from commits since last tag
bash changelog.sh

# Or use the Claude Code skill
/generate-changelog
```

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-08-21

### Added
- OAuth2 login flow ([a1b2c3d](https://github.com/owner/repo/commit/a1b2c3d))
- User profile settings page ([e4f5g6h](https://github.com/owner/repo/commit/e4f5g6h))

### Fixed
- Null pointer in user endpoint ([i7j8k9l](https://github.com/owner/repo/commit/i7j8k9l))

### Changed
- Migrate to connection pooling ([m0n1o2p](https://github.com/owner/repo/commit/m0n1o2p))

### Removed
- Drop legacy v1 endpoints ([q3r4s5t](https://github.com/owner/repo/commit/q3r4s5t))
```
