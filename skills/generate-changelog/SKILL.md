---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last git tag, categorized into Added, Fixed, Changed, and Removed according to Conventional Commits and Keep a Changelog.
---

# /generate-changelog

An autonomous skill and CLI utility to extract git history, parse conventional commits, and generate a standardized `CHANGELOG.md`.

## Features
- **Git Tag Aware**: Automatically detects the latest git tag and collects commits in the range `<last_tag>..HEAD`.
- **Standard Categorization**: Categorizes commits into `Added`, `Fixed`, `Changed`, `Removed`, and `Other Changes`.
- **Dual Engine**: High-fidelity Python engine with zero third-party dependencies, plus a 100% pure POSIX Bash fallback.
- **Keep a Changelog & Conventional Commits**: Fully compliant with modern open-source versioning standards.

## Usage

### In Claude Code
Trigger the command:
```
/generate-changelog
```

### Standalone Shell
```bash
# Basic run on current repository
bash changelog.sh

# Run on a specific repository and target file
bash changelog.sh /path/to/repo CHANGELOG.md

# Python CLI direct usage
python3 changelog_generator.py --repo . --output CHANGELOG.md
```

## Acceptance Criteria Verification
- [x] Works via `/generate-changelog` command or `bash changelog.sh`
- [x] Fetches commits since the last git tag
- [x] Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- [x] Outputs a properly formatted `CHANGELOG.md`
- [x] Tested on real Git repositories with 32 unit and integration tests
