# Changelog Generator

Generates a structured `CHANGELOG.md` from git history since the last tag.

## Setup (3 steps)

```bash
# 1. Enter your git repository
cd /your/project

# 2. Run the generator (choose one)
python3 skills/changelog-generator/changelog.py
bash   skills/changelog-generator/changelog.sh

# 3. View the result
cat CHANGELOG.md
```

## Usage

### Python

```bash
# Default output: CHANGELOG.md
python3 skills/changelog-generator/changelog.py

# Custom output file
python3 skills/changelog-generator/changelog.py --output HISTORY.md

# Limit number of commits
python3 skills/changelog-generator/changelog.py --limit 20
```

### Bash

```bash
bash skills/changelog-generator/changelog.sh
bash skills/changelog-generator/changelog.sh HISTORY.md
```

### Claude Code

```
/generate-changelog
```

## Fallback behavior

If there is no git tag, the script reads from the first commit to HEAD.
If the latest tag is at HEAD, it falls back to the previous tag.

## Output

Writes to `CHANGELOG.md` (or the specified filename) in the current directory.
Commits are categorized as **Added**, **Fixed**, **Changed**, or **Removed**.
Uncategorized commits appear under **Uncategorized**.

## Test

```bash
bash skills/changelog-generator/test_changelog_generator.sh
```

## Output example

```
# Changelog

## Added
- feat: add search feature

## Fixed
- fix: resolve timeout

## Changed
- chore: bump version to 1.1.0
```
