---
name: generate-changelog
description: Automatically generates or updates a Keep a Changelog formatted CHANGELOG.md from git history since the latest tag.
---

# Generate Structured CHANGELOG Skill

Use this skill whenever asked to generate, update, or inspect a changelog for a repository using git history.

## How it works
1. Runs `git describe --tags --abbrev=0` to identify the most recent release tag.
2. Extracts git commits in the range `${LAST_TAG}..HEAD` (or all commits if no tags exist).
3. Automatically classifies each commit message into Keep a Changelog categories:
   - **Added**: new features, capabilities, or files (`feat`, `add`, `new`)
   - **Fixed**: bug fixes, patches, issue resolutions (`fix`, `bug`, `patch`)
   - **Changed**: updates, refactors, dependencies, performance (`change`, `refactor`, `perf`, `chore`)
   - **Removed**: deletions, deprecations (`remove`, `delete`, `deprecated`)
4. Prepends the structured section into `CHANGELOG.md` with commit hashes and clean descriptions.

## Usage
Run directly from terminal or Claude Code prompt:
```bash
bash changelog.sh
```
or target a specific repository path:
```bash
bash changelog.sh /path/to/repo
```
