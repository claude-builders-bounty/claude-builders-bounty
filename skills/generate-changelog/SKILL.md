---
name: generate-changelog
description: Automatically generates and updates structured CHANGELOG.md from git commit history since the last tag.
version: 1.0.0
tags: [git, changelog, documentation, release]
---

# Generate Changelog Skill

When invoked via `/generate-changelog [version]` or requested by the user, this skill:
1. Identifies the latest git tag using `git describe --tags --abbrev=0`.
2. Inspects commits between `<last-tag>..HEAD` (or all commits if no tags exist).
3. Automatically classifies commit messages into standard sections:
   - `Added`: Features and new capabilities (`feat:`, `add:`)
   - `Fixed`: Bug repairs and patches (`fix:`, `bug:`)
   - `Changed`: Refactors, tooling, performance, and chores (`refactor:`, `chore:`, `perf:`)
   - `Removed`: Deprecated and deleted code (`remove:`, `delete:`)
4. Generates or prepends the formatted release notes to `CHANGELOG.md`.

## Execution

```bash
python3 changelog.py --version "v1.0.0"
```
