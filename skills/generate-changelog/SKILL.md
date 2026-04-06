# /generate-changelog

Generate a structured CHANGELOG.md from git history using conventional commits.

## Instructions

When the user invokes `/generate-changelog`, follow these steps:

### 1. Detect tags and commit ranges

Run the following to find all version tags (sorted newest first):

```bash
git tag -l --sort=-version:refname
```

If there are tags, group commits between consecutive tags. If there are no tags, treat all commits as "Unreleased".

### 2. Fetch commits

For each range (tag-to-tag or tag-to-HEAD), fetch commit subjects:

```bash
git log <range> --pretty=format:"%s" --no-merges
```

### 3. Categorize commits

Map conventional commit prefixes to Keep a Changelog sections:

| Prefix | Section |
|--------|---------|
| `feat:` / `feat(...):`   | **Added**   |
| `fix:` / `fix(...):`     | **Fixed**   |
| `refactor:`, `perf:`, `style:`, `chore:`, `ci:`, `build:`, `docs:` | **Changed** |
| `revert:`, `remove:`, `deprecate:` | **Removed** |
| _(no prefix)_            | **Changed** |

### 4. Generate the changelog

Write a `CHANGELOG.md` in the repo root with this structure:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Conventional Commits](https://www.conventionalcommits.org/).

## Unreleased

### Added
- Description of new feature

### Fixed
- Description of bug fix

## v1.0.0 (2025-01-15)

### Added
- Initial release features
```

### 5. Alternative: use the bash script

If the user prefers a non-interactive approach, run:

```bash
bash skills/generate-changelog/changelog.sh
```

Options:
- `--output FILE` — write to a custom path
- `--stdout` — print to stdout instead of writing a file
- `--from TAG` — only include commits since TAG
- `--repo DIR` — run against a different repository

## Examples

```
User: /generate-changelog
→ Generates CHANGELOG.md from full git history

User: /generate-changelog --from v2.0.0
→ Generates changelog starting from v2.0.0

User: /generate-changelog --stdout
→ Prints changelog to terminal without writing a file
```
