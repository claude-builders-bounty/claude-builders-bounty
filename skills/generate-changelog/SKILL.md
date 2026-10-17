---
name: generate-changelog
description: Automatically generates or updates a structured Keep-a-Changelog CHANGELOG.md from git commit history since the latest tag.
---

# Generate Changelog Skill 📝

Generate a structured `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) standard by inspecting git commits since the last release tag.

## When to Use

Invoke this skill whenever:
- Preparing a new release or tagging a version.
- Reviewing recent merged PRs and commit activity.
- Updating `CHANGELOG.md` with unreleased changes.

## Commands

Run the generator directly using python or the provided bash wrapper:

```bash
# Print changelog to terminal
python skills/generate-changelog/scripts/changelog.py --dry-run

# Write or prepend to CHANGELOG.md for a specific version
python skills/generate-changelog/scripts/changelog.py --version "v1.2.0" --output CHANGELOG.md

# Generate changes since a specific tag or commit
python skills/generate-changelog/scripts/changelog.py --since "v1.1.0" --output CHANGELOG.md
```

## Commit Categorization

Commits are parsed according to Conventional Commits:

| Conventional Commit Prefix | Keep a Changelog Section |
|----------------------------|--------------------------|
| `feat:`, `add:`            | `Added`                  |
| `fix:`, `bugfix:`          | `Fixed`                  |
| `refactor:`, `perf:`, `chore:`, `style:` | `Changed` |
| `remove:`, `delete:`, `deprecate:` | `Removed`      |
| `docs:`, `doc:`            | `Documentation`          |
| `security:`, `sec:`        | `Security`               |
| Other messages             | `Other`                  |

Scoped prefixes (`feat(auth): add OAuth login`) automatically bold the scope name (`- **auth**: add OAuth login`).
