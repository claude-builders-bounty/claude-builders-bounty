---
name: generate-changelog
description: Automatically generates or updates a structured CHANGELOG.md from git commits since the last tag, categorized into Added, Fixed, Changed, and Removed.
---

# Generate Changelog Skill

Use this skill to inspect repository commit history and generate or update `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Conventional Commits](https://www.conventionalcommits.org/) standards.

## Usage

Run the generator from the root of any git repository:

```bash
# Basic run: detects latest git tag and updates CHANGELOG.md
bash changelog.sh

# Or directly with Python
python3 generate_changelog.py

# Specify custom version or release name
bash changelog.sh --version "v1.2.0"

# Preview output in console without modifying CHANGELOG.md
bash changelog.sh --dry-run

# Specify custom baseline tag or commit
bash changelog.sh --since "v1.0.0" --version "v1.1.0"
```

## How It Works

1. **Tag Discovery**: Finds the most recent git tag using `git describe --tags --abbrev=0`. If no tag exists, falls back to the initial commit.
2. **Log Extraction**: Retrieves all commits within `<tag>..HEAD` with authors and short hashes.
3. **Smart Categorization**:
   - `Added`: Commits starting with `feat:`, `feature:`, `add:` or containing additions.
   - `Fixed`: Commits starting with `fix:`, `bugfix:`, `hotfix:`, `patch:`.
   - `Removed`: Commits starting with `remove:`, `delete:`, `deprecate:`.
   - `Changed`: Commits starting with `chore:`, `refactor:`, `perf:`, `docs:`, `update:`.
4. **Markdown Formatting**: Generates clean bullet points formatted with commit hashes and author credits. Prepend cleanly to `CHANGELOG.md`.
