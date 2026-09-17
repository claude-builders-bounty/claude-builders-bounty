---
name: generate-changelog
description: Automatically generates and updates a structured CHANGELOG.md from git history, categorized into Added, Fixed, Changed, and Removed according to the Keep a Changelog standard.
triggers:
  - /generate-changelog
  - generate changelog
  - update changelog
---

# Generate Changelog Skill

This skill extracts commits since the last git tag (or initial commit) and synthesizes a structured release section into `CHANGELOG.md`.

## Execution Workflow

1. **Inspect Tags and History**:
   - Queries `git describe --tags --abbrev=0` for the baseline release point.
   - Extracts all non-merge commits up to `HEAD`.

2. **Categorize Commits**:
   - `Added`: Feature additions (`feat:`, `add:`, `create:`, `implement:`)
   - `Fixed`: Bug resolutions (`fix:`, `patch:`, `resolve:`, `close #...`)
   - `Changed`: Updates, refactors, docs, CI (`refactor:`, `perf:`, `docs:`, `update:`)
   - `Removed`: Deprecations and cleanups (`remove:`, `delete:`, `deprecate:`)

3. **Format & Write**:
   - Prepends release block into `CHANGELOG.md` adhering to Keep a Changelog standards.

## Usage

```bash
# Generate for unreleased changes
bash skills/generate-changelog/changelog.sh

# Generate for a specific release tag/version
bash skills/generate-changelog/changelog.sh v1.2.0
```
