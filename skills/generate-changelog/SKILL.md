---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag, with commit categorization and safe fallbacks.
---

# Generate Changelog

Use this skill when a repository needs a structured `CHANGELOG.md` generated from recent git history.

## What It Does

- Finds the latest reachable git tag.
- Reads commits since that tag, or all commits when no tag exists.
- Categorizes commits into Added, Changed, Fixed, Removed, Security, Deprecated, and Other.
- Writes a Markdown changelog section with commit hashes and subjects.
- Preserves existing changelog content by prepending the new section.

## Quick Start

```bash
python skills/generate-changelog/scripts/generate_changelog.py
```

Optional arguments:

```bash
python skills/generate-changelog/scripts/generate_changelog.py --output CHANGELOG.md
python skills/generate-changelog/scripts/generate_changelog.py --from v1.2.0 --to HEAD
python skills/generate-changelog/scripts/generate_changelog.py --dry-run
```

## Acceptance Checklist

- Run the command from the root of a git repository.
- Confirm the generated sections match the commit history.
- Move any uncategorized commits from Other into a better section if needed.
- Review before release; automated categorization is intentionally conservative.
