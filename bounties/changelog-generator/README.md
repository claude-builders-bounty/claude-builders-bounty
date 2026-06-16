# 🪵 Changelog Generator

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Quick Start

```bash
# 1. Clone this skill
git clone <this-repo> changelog-skill
cd changelog-skill

# 2. Run it
bash changelog.sh

# 3. Done — open CHANGELOG.md
```

## Usage

```bash
# Generate for current directory
bash changelog.sh

# Generate for a specific repo path
bash changelog.sh --repo /path/to/project

# Generate with custom output file
bash changelog.sh --output CHANGES.md

# Generate from a specific tag
bash changelog.sh --since v1.0.0
```

## Claude Code Integration

This skill adds a `/generate-changelog` command to Claude Code:

```markdown
<!-- SKILL.md -->
/generate-changelog — Generate structured CHANGELOG.md from git history
  Usage: /generate-changelog [--repo PATH] [--output FILE] [--since TAG]

Automatically categorizes commits into:
- **Added** — new features (feat:, add:, new:)
- **Fixed** — bug fixes (fix:, bugfix:, patch:)
- **Changed** — updates, refactors, improvements
- **Removed** — deletions, deprecations
- **Deprecated** — deprecation warnings
- **Security** — security fixes

Outputs a clean `CHANGELOG.md` with linked commit hashes.
```

## Sample Output

```markdown
# Changelog

## [v1.2.0] - 2026-06-15

### Added
- New payment processing pipeline ([a1b2c3d](https://github.com/user/repo/commit/a1b2c3d))
- User authentication with OAuth2 ([e4f5g6h](https://github.com/user/repo/commit/e4f5g6h))

### Fixed
- Race condition in concurrent requests ([i7j8k9l](https://github.com/user/repo/commit/i7j8k9l))
- Memory leak in websocket handler ([m0n1o2p](https://github.com/user/repo/commit/m0n1o2p))

### Changed
- Upgraded dependencies to latest versions ([q3r4s5t](https://github.com/user/repo/commit/q3r4s5t))
- Refactored database access layer ([u6v7w8x](https://github.com/user/repo/commit/u6v7w8x))
```

## Requirements

- `bash` 4.0+
- `git` 2.0+

Works on macOS, Linux, and Windows (Git Bash / WSL).

## How It Works

1. Finds the most recent git tag (or all commits if no tags exist)
2. Reads commit messages since that tag
3. Categorizes each commit based on conventional commit prefixes
4. Generates a structured, ready-to-publish CHANGELOG.md
