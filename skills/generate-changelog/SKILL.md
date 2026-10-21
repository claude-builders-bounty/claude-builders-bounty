---
name: generate-changelog
description: Automatically generate a structured Keep a Changelog Markdown document from git commit history and conventional commits.
---

# generate-changelog

Generate a structured `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Conventional Commits](https://www.conventionalcommits.org/).

## Usage

Run the tool from the repository root:

```bash
# Generate changelog for commits since latest git tag
./changelog.sh

# Or invoke python CLI directly
python3 bin/generate-changelog --repo . --version 1.0.0

# Generate full historical changelog across all tags
python3 bin/generate-changelog --all-releases -o CHANGELOG.md
```

## Categorization Rules

The generator maps commits into sections:
- `feat:` or `feature:` → **Added**
- `fix:`, `bugfix:`, `hotfix:` → **Fixed**
- `perf:`, `refactor:`, `style:` → **Changed**
- `revert:`, `remove:`, `deprecate:` → **Removed**
- `docs:` → **Documentation**
- `chore:`, `ci:`, `build:`, `test:` → **Maintenance**
- Commits with `!` (e.g. `feat!:`) or `BREAKING CHANGE:` → **Breaking Changes**
