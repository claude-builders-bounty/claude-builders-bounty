---
name: generate-changelog
description: Automatically inspects git commit history since the latest tag and generates a structured, categorized CHANGELOG.md adhering to Keep a Changelog standards.
tools:
  - bash
---

# Generate Changelog Skill

A production-grade skill and automation engine that extracts git commit history and generates or updates a standardized `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## Overview

This skill analyzes commit history since the latest git tag (or from repository origin if unreleased) and organizes entries into standardized categories:
- **`Added`**: New user-facing features and endpoints.
- **`Fixed`**: Bug fixes, security patches, and issue resolutions.
- **`Changed`**: Enhancements, refactors, dependency updates, and performance optimizations.
- **`Removed`**: Deprecated or deleted functionality.
- **`Security`**: Vulnerability mitigations and audit fixes.

Breaking changes (e.g. `feat!:`, `BREAKING CHANGE:`) are automatically flagged with warning badges for release transparency.

---

## Invocation

### Method 1: Claude Code Slash Command
Inside Claude Code, run:
```bash
/generate-changelog
```
The agent executes the generator, reads recent git commits, writes the new release block, and presents the formatted summary for review.

### Method 2: Cross-Platform Python CLI
```bash
# Basic run (updates CHANGELOG.md automatically)
python skills/generate-changelog/changelog.py

# Specify explicit release version tag
python skills/generate-changelog/changelog.py --version v1.2.0

# Export structured JSON for CI/CD pipelines
python skills/generate-changelog/changelog.py --format json --output release-notes.json

# Filter commit range
python skills/generate-changelog/changelog.py --since 2026-01-01 --until HEAD
```

### Method 3: POSIX Bash CLI
```bash
# Basic usage
bash skills/generate-changelog/changelog.sh

# With custom output file and release title
bash skills/generate-changelog/changelog.sh CHANGELOG.md v1.2.0
```

---

## Commit Classification Standards

The skill recognizes both Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `perf:`, `test:`, `revert:`) and natural language commit patterns:

| Commit Prefix / Keyword | Changelog Category | Example |
| :--- | :--- | :--- |
| `feat:`, `feat(...)`, `add:`, `new:` | **Added** | `feat(auth): add OAuth2 PKCE login support` |
| `fix:`, `fix(...)`, `bug:`, `patch:` | **Fixed** | `fix(api): resolve race condition in token refresh` |
| `perf:`, `refactor:`, `update:`, `change:` | **Changed** | `perf(db): add index on tenant_id query planner` |
| `remove:`, `drop:`, `delete:`, `deprecate:` | **Removed** | `remove(legacy): drop deprecated v1 webhook handler` |
| `sec:`, `security:`, `cve:` | **Security** | `sec(headers): enforce strict Content-Security-Policy` |

---

## Edge Case Handling

1. **Greenfield Repositories**: If no prior tags exist, all commits from root commit are captured under `[Unreleased]`.
2. **Merge Commits**: Automated merge bubble commits (`Merge pull request #...`) are filtered out to maintain clean release notes.
3. **Existing CHANGELOG Preservation**: New release sections are prepended directly beneath the main header, preserving full historical release entries without clobbering.
4. **CI/CD Integration**: Supports `--format json` for integration into GitHub Actions, semantic release bots, and Slack/Discord release notifications.
