---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, auto-categorizing commits into Added/Fixed/Changed/Removed sections following Keep a Changelog format
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from the project's git history.

## Steps

### 1. Determine the commit range

Run this command to find the latest git tag:

```bash
git describe --tags --abbrev=0 2>/dev/null
```

- If a tag is found, use it as the starting point: commits from `<tag>..HEAD`
- If no tags exist, use the entire commit history

### 2. Fetch the commit log

Run the appropriate command (based on whether a tag was found):

```bash
# With a tag:
git log <tag>..HEAD --pretty=format:"%h  %s" --no-merges

# Without a tag:
git log --pretty=format:"%h  %s" --no-merges
```

### 3. Categorize every commit

Place each commit into exactly one of these four categories:

| Category    | Conventional Prefixes              | Keyword Signals                                         |
|-------------|------------------------------------|---------------------------------------------------------|
| **Added**   | `feat`, `add`, `new`               | add, create, introduce, implement, support, enable      |
| **Fixed**   | `fix`, `bugfix`, `patch`, `hotfix` | fix, resolve, repair, correct, close                    |
| **Changed** | `refactor`, `update`, `improve`, `perf`, `style`, `enhance`, `chore`, `ci`, `build`, `docs`, `test` | update, improve, refactor, change, modify, bump |
| **Removed** | `remove`, `delete`, `drop`, `deprecate`, `revert` | remove, delete, strip, drop, purge, revert    |

**Priority:** Match conventional commit prefix first (e.g., `feat:`, `fix(scope):`). If no prefix is detected, analyze the full commit message for keyword signals. If still ambiguous, default to **Changed**.

**Display:** Strip the conventional commit prefix from the display text. Capitalize the first letter of the cleaned message.

### 4. Write CHANGELOG.md

Use the **Write** tool to create `CHANGELOG.md` in the project root with this exact format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] (since <tag>) — <YYYY-MM-DD>

### Added

- <cleaned commit message> (`<short hash>`)

### Fixed

- <cleaned commit message> (`<short hash>`)

### Changed

- <cleaned commit message> (`<short hash>`)

### Removed

- <cleaned commit message> (`<short hash>`)
```

**Rules:**
- Only include category sections that have at least one entry
- Use today's date in YYYY-MM-DD format
- If no tag exists, omit the "(since <tag>)" part from the header
- Each entry is a single line: `- <message> (\`<hash>\`)`
- Leave one blank line between each section

### 5. Report results

After writing the file, tell the user:
- How many commits were processed
- The breakdown by category (Added/Fixed/Changed/Removed)
- The tag range used (or "all commits" if no tag)
