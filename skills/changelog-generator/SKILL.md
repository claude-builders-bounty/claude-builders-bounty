---
name: changelog-generator
description: Generate a structured CHANGELOG.md from git history, grouped by Conventional Commit categories.
---

# Changelog Generator

Use this skill when a user asks for a changelog, release notes, or a summary of commits since a tag or date.

## Workflow

1. Inspect the repository history with `git log`.
2. Run the generator:

```bash
python skills/changelog-generator/generate_changelog.py --output CHANGELOG.md
```

3. Review the generated sections and edit any product-facing wording before release.

## Options

```bash
python skills/changelog-generator/generate_changelog.py --since v1.2.0 --output CHANGELOG.md
python skills/changelog-generator/generate_changelog.py --max-count 50
```

## Categories

- Added: `feat`, `add`
- Fixed: `fix`, `hotfix`
- Changed: `change`, `refactor`, `perf`, `deps`, `build`, `ci`
- Removed: `remove`, `delete`, `drop`
- Documentation: `docs`
- Tests: `test`
- Other: uncategorized commits
