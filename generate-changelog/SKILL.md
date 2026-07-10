---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag. Use when the user runs /generate-changelog or asks to create or update a changelog from commits.
---

# Generate Changelog

Produce a Keep-a-Changelog-style `CHANGELOG.md` from git commits since the latest tag, categorized into **Added**, **Fixed**, **Changed**, and **Removed**.

## Instructions

1. Confirm the current directory is inside a git repository (`git rev-parse --show-toplevel`).
2. Run the bundled script (prefer the path relative to this skill):

```bash
bash "$(dirname "$0")/changelog.sh" CHANGELOG.md
```

If the skill directory is not available as `$0`, run the copy shipped with the project:

```bash
bash generate-changelog/changelog.sh CHANGELOG.md
# or, if installed at repo root:
bash changelog.sh CHANGELOG.md
```

3. Show the user the generated file path and a short summary of how many commits were categorized into each section.
4. Do not invent commits. Only use git history produced by the script.

## Categorization rules (implemented in `changelog.sh`)

| Section   | Conventional types / keywords                          |
|-----------|--------------------------------------------------------|
| Added     | `feat`, add, create, introduce, implement, new         |
| Fixed     | `fix`, bugfix, hotfix, bug, patch, resolve           |
| Removed   | `remove`, delete, drop, deprecate                      |
| Changed   | `chore`, `docs`, `refactor`, `perf`, update, and other |

## Output format

```markdown
# Changelog

## [Unreleased (since v1.2.0)]

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Refactor description

### Removed
- Removed API description
```

Empty categories are omitted.
