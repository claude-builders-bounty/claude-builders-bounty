---
name: git-changelog-skill
description: Generates a structured CHANGELOG.md from git commit history
---



# SKILL: Generate Changelog

## Trigger
Use this skill when the user runs `/generate-changelog` or asks to generate a changelog from git history.

## What This Skill Does
Generates a structured `CHANGELOG.md` from git commit history since the last tag,
auto-categorizing commits into: **Added**, **Fixed**, **Changed**, **Removed**.

---

## Step-by-Step Execution

### 1. Confirm Git Repo
```bash
git rev-parse --is-inside-work-tree
```
If this fails, stop and tell the user to run from inside a git project.

### 2. Find Last Tag
```bash
git describe --tags --abbrev=0 2>/dev/null || echo "NO_TAGS"
```
- If a tag exists, store it as `$LAST_TAG` and set range to `$LAST_TAG..HEAD`
- If no tags, use full history (no range filter)

### 3. Fetch Commits
```bash
git log $LAST_TAG..HEAD --pretty=format:"%s" --no-merges
```
(Drop `$LAST_TAG..HEAD` if no tags exist.)

### 4. Categorize Each Commit Subject

Apply these rules **in order** — first match wins:

| Category  | Trigger keywords / prefixes |
|-----------|----------------------------|
| **Added**   | `feat`, `add`, `new`, `create`, `introduce`, `implement` |
| **Fixed**   | `fix`, `bug`, `patch`, `resolve`, `hotfix`, `correct`, `revert` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate` |
| **Changed** | `refactor`, `update`, `change`, `improve`, `upgrade`, `bump`, `style`, `perf`, `chore`, `build`, `ci`, `docs`, `test` |
| **Other**   | Everything else |

Strip conventional-commit prefixes before display:
`feat(auth): add login` → `add login`

### 5. Write CHANGELOG.md

Use this exact format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] — YYYY-MM-DD
*(changes since <last-tag>)*

### Added
- <entry>

### Fixed
- <entry>

### Changed
- <entry>

### Removed
- <entry>
```

Only include sections that have at least one entry.
Preserve any existing previous-version sections below the new entry.

### 6. Report to User

After writing the file, summarize:
- Path of the output file
- Count per category
- Tag range used

---

## Quick-Run Alternative
If the user just wants to run it immediately, execute:
```bash
bash changelog.sh
```
(The script must exist in the repo root. If it doesn't, create it from the template in this skill first.)

---

## Options
| Flag | Description |
|------|-------------|
| `--since <tag>` | Override the starting tag |
| `--output <file>` | Write to a different file (default: `CHANGELOG.md`) |
| `--version <label>` | Label for the new section (default: `Unreleased`) |

## Example
```bash
bash changelog.sh --since v1.2.0 --version 1.3.0
```