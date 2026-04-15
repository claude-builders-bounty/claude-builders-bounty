---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history with auto-categorization
version: 1.0.0
author: xamdkx
---

# /generate-changelog

Generate a structured `CHANGELOG.md` from your git history. Commits are auto-categorized into **Added**, **Fixed**, **Changed**, **Removed**, **Security**, and **Performance** sections using Conventional Commits prefixes and keyword detection.

## Usage

```
/generate-changelog                  # Since last git tag
/generate-changelog v1.0.0           # Since a specific tag
/generate-changelog v1.0.0 v2.0.0    # Between two tags
/generate-changelog --all            # Full history
```

## How it works

1. Reads git log since the last tag (or specified range)
2. Parses each commit message for Conventional Commits prefixes (`feat:`, `fix:`, `refactor:`, etc.)
3. Falls back to keyword detection (`added`, `fixed`, `removed`, `security`, `performance`, etc.)
4. Generates a properly formatted CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format
5. Includes commit hash, author, and date for each entry
6. Appends summary stats (total commits, contributors)

## Categories

| Prefix/Keyword | Category |
|----------------|----------|
| `feat:`, `add`, `new`, `implement` | Added |
| `fix:`, `bug`, `hotfix`, `patch` | Fixed |
| `refactor:`, `chore:`, `update`, `improve` | Changed |
| `remove`, `delete`, `deprecated`, `drop` | Removed |
| `security`, `vuln`, `CVE`, `XSS` | Security |
| `perf:`, `optimize`, `cache`, `faster` | Performance |

## Bonus features

- Skips merge commits automatically
- Works with any git repository (no config needed)
- Supports tag ranges for release-specific changelogs
- Includes contributor count in footer
- Follows [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/)
