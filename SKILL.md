---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history using Conventional Commits"
version: 1.0.0
author: claude-builders-bounty
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from your project's git history. Commits
are automatically categorized by their Conventional Commit prefix.

## Usage

In any git repository, run:

```
/generate-changelog
```

Or from the command line:

```bash
bash changelog.sh -o CHANGELOG.md
```

## Examples

```bash
# All commits since the last tag
bash changelog.sh

# Commits since a specific tag
bash changelog.sh --since v1.0.0

# Commits within a date range
bash changelog.sh --since 2025-01-01 --until 2025-03-31

# Output to file with a version heading
bash changelog.sh --output CHANGELOG.md --version 1.1.0

# Run against a different repo
bash changelog.sh --repo /path/to/project

# Specify a release date
bash changelog.sh --output CHANGELOG.md --version 2.0.0 --date 2025-06-15
```

## How It Works

1. Fetches commits since the last git tag (or your specified range)
2. Parses Conventional Commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
3. Categorizes into: **Added** / **Fixed** / **Changed** / **Removed** / **Documentation** / **Tests** / **CI & Build**
4. Detects breaking changes from `!` prefix and `BREAKING CHANGE` footers
5. Outputs a clean, well-formatted CHANGELOG.md

## Categorization

| Prefix | Section |
|--------|---------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:`, `update:` | Changed |
| `remove:`, `revert:`, `deprecate:` | Removed |
| `docs:` | Documentation |
| `test:` | Tests |
| `ci:`, `build:`, `chore:` | CI & Build |
| `merge:`, `wip:` | Skipped |


