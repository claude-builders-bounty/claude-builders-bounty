---
name: generate-changelog
description: Generate a structured Keep-a-Changelog compatible CHANGELOG.md from git commits since the last tag.
disable-model-context: false
---

# /generate-changelog

Extracts git commit history since the most recent git tag (or from inception if no tag exists), categorizes each commit into `Added`, `Fixed`, `Changed`, and `Removed`, and formats or updates `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standards.

## Usage

Run directly in any repository root:

```bash
python3 skills/generate-changelog/generate_changelog.py
```
or
```bash
bash skills/generate-changelog/changelog.sh
```

## How It Works

1. **Tag Detection**: Finds the latest tag via `git describe --tags --abbrev=0`.
2. **Commit Extraction**: Parses commits with `git log <tag>..HEAD --no-merges`.
3. **Categorization Rules**:
   - `Added`: Commits prefixed with `feat:`, `feature:`, `Add...`, `Create...`.
   - `Fixed`: Commits prefixed with `fix:`, `bug:`, `hotfix:`, `Fix...`, `Resolve...`.
   - `Removed`: Commits prefixed with `remove:`, `revert:`, `Remove...`, `Delete...`.
   - `Changed`: Commits prefixed with `refactor:`, `perf:`, `docs:`, `chore:`, `style:`, `Update...`.
4. **Markdown Generation**: Prepends or inserts the categorized release section into `CHANGELOG.md` preserving previous entries.
