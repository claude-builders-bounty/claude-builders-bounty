---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from a project's git history using Conventional Commits"
version: 1.0.0
author: Claude Builders Bounty
---

# Generate CHANGELOG

A Claude Code skill that generates a structured `CHANGELOG.md` from a project's git history, parsing Conventional Commit messages and organizing changes into labeled sections.

## Usage

```bash
# Generate CHANGELOG.md in current directory
/generate-changelog

# Generate to a custom file
/generate-changelog --output RELEASE.md

# Generate from a specific tag onwards
/generate-changelog --from-tag v1.0.0
```

Or directly:
```bash
python3 generate-changelog.py
```

## Features

- **Conventional Commit parsing** — automatically categorizes feat, fix, refactor, docs, test, etc.
- **Release grouping** — groups changes since the last git tag
- **Emoji labels** — visual category headers (✨ Added, 🐛 Fixed, ♻️ Changed, etc.)
- **Priority ordering** — most important sections first
- **Configurable output** — custom file path, version, and date

## Output Example

```markdown
# Changelog

## [v2.0.0] - 2026-05-06

> **12 changes** in this release

### ✨ Added
- User authentication via OAuth ([`a1b2c3d`])
- Dark mode toggle ([`e4f5g6h`])

### 🐛 Fixed
- Login redirect loop ([`i7j8k9l`])
- Mobile layout overflow ([`m0n1o2p`])
```

## Requirements

- Python 3.8+
- Git repository
