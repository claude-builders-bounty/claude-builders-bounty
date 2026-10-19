---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history, categorized into Added, Fixed, Changed, and Removed sections based on Conventional Commits.
---

# Generate Changelog Skill 📝

Use this skill whenever the user or developer asks to generate, update, or preview a `CHANGELOG.md` based on git commits.

## Slash Command Usage

When invoked via `/generate-changelog [version]`, execute the bundled script:

```bash
skills/generate-changelog/changelog.sh --version "$VERSION"
```

## How It Works

1. **Tag Detection:** Identifies the latest git tag using `git describe --tags --abbrev=0`.
2. **Commit Parsing:** Extracts all commits since that tag (or all project commits if no tags exist).
3. **Smart Categorization:**
   - `feat`, `add` -> `### Added`
   - `fix`, `bug`, `patch` -> `### Fixed`
   - `perf`, `refactor`, `update`, `chore`, `docs` -> `### Changed`
   - `remove`, `deprecate`, `delete` -> `### Removed`
4. **Keep a Changelog Formatting:** Generates or prepends to `CHANGELOG.md` with links to commit hashes and authors.
