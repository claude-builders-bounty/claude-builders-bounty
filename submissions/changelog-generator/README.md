# CHANGELOG Generator

Auto-generates a structured `CHANGELOG.md` from your project's git history.

## Setup (1 step)

```bash
curl -sL https://raw.githubusercontent.com/laogongcy-del/claude-builders-bounty/main/submissions/changelog-generator/changelog.sh -o changelog.sh && chmod +x changelog.sh
```

## Usage (1 command)

```bash
# Default: writes to CHANGELOG.md
bash changelog.sh

# Custom output path
bash changelog.sh docs/HISTORY.md
```

## What it does

- Finds the last git tag to determine the commit range (or all commits if no tags exist)
- Fetches all commits since that tag
- Auto-categorizes into: **Added**, **Fixed**, **Changed**, **Removed**, **Security**, **Deprecated**
- Supports both conventional commits (`feat:`, `fix:`, `chore:`, etc.) and keyword-based detection
- Generates clean, well-formatted Markdown
- Links commits to GitHub when a remote origin is detected

## Sample output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [unreleased] — 2026-06-12 since v1.2.0

### Added
  - [a1b2c3d](https://github.com/owner/repo/commit/a1b2c3d) User dashboard with team switcher
  - [e4f5g6h](https://github.com/owner/repo/commit/e4f5g6h) Export reports as CSV

### Fixed
  - [i7j8k9l](https://github.com/owner/repo/commit/i7j8k9l) Login redirect loop when session expires

### Changed
  - [m0n1o2p](https://github.com/owner/repo/commit/m0n1o2p) Upgrade Drizzle ORM to v0.38
  - [q3r4s5t](https://github.com/owner/repo/commit/q3r4s5t) Refactor API error handling

### Removed
  - [u6v7w8x](https://github.com/owner/repo/commit/u6v7w8x) Drop deprecated v1 API endpoints
```
