---
name: generate-changelog
description: Automatically analyzes git commit history since the previous release/tag and generates or prepends a Keep a Changelog compliant CHANGELOG.md categorized into Added, Fixed, Changed, and Removed sections.
---

# Generate Structured Git Changelog

This skill analyzes the project's git history since the latest git tag (or from inception if un-tagged) and generates a structured, human-readable `CHANGELOG.md` conforming to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standards.

## Usage

Run via slash command:
```
/generate-changelog [optional: version_name]
```

Or execute directly from the terminal:
```bash
# Using Python CLI (Cross-platform: Windows, Linux, macOS)
python scripts/generate_changelog.py --version "v1.0.0"

# Using Bash script
bash changelog.sh
```

## How It Works

1. **Tag Detection**: Finds the most recent git tag via `git describe --tags --abbrev=0`.
2. **Commit Isolation**: Extracts all non-merge commits between the latest tag and `HEAD`.
3. **Categorization**: Auto-sorts each commit into standard Keep a Changelog categories:
   - **`Added`**: New features, capabilities (`feat:`, `feature:`, `add:`, or "introduce/support" keywords).
   - **`Fixed`**: Bug fixes, patches (`fix:`, `bugfix:`, `hotfix:`, or "resolve" keywords).
   - **`Changed`**: Enhancements, refactors, docs, perf (`refactor:`, `perf:`, `docs:`, `chore:`).
   - **`Removed` / `Deprecated`**: Deprecations or deletions (`remove:`, `deprecate:`, `revert:`).
4. **Markdown Formatting**:
   - Formats clean bullet points with capitalized descriptions and commit hash links (`[`hash`]`).
   - If `CHANGELOG.md` already exists, neatly prepends the new release section below the header while preserving historical releases.
   - If no `CHANGELOG.md` exists, creates the standard header and SemVer preamble.

## CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--repo <path>` | `.` | Root path of the target git repository |
| `--version <str>` | `Unreleased` | Version title header to display |
| `--output <file>` | `CHANGELOG.md` | Target changelog markdown file path |
| `--dry-run` | `False` | Prints formatted markdown to stdout without writing to disk |
