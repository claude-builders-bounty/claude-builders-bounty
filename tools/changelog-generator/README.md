# Structured changelog generator

This directory contains a Bash changelog generator for bounty #1.

It creates a Markdown `CHANGELOG.md` from git history and auto-categorizes commits into:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

## Setup and usage in 3 steps

1. Copy the script into a git repository:

   ```bash
   cp tools/changelog-generator/changelog.sh /path/to/repo/changelog.sh
   ```

2. Run it from the repository root:

   ```bash
   bash changelog.sh
   ```

3. Review the generated file:

   ```bash
   less CHANGELOG.md
   ```

## Options

```bash
bash changelog.sh --help
bash changelog.sh --output CHANGELOG.md
bash changelog.sh --since v1.2.0 --output CHANGELOG.md
bash changelog.sh --repo /path/to/repo --output CHANGELOG.md
```

## Behavior

- Uses commits since the latest git tag by default.
- If the repository has no tags, uses all commits.
- Ignores merge commits to keep the output focused on authored changes.
- Writes a Keep a Changelog-style Markdown file.
- Includes commit hash and date for traceability.

## Categorization rules

The script uses practical conventional-commit style heuristics:

- Added: `feat:`, `feature:`, `add:`, `added:`, `new:`, and similar add/introduce wording.
- Fixed: `fix:`, `bug:`, `bugfix:`, `hotfix:`, `patch:`, and similar fix/bug wording.
- Changed: `change:`, `update:`, `refactor:`, `perf:`, `docs:`, `test:`, `chore:`, `ci:`, `style:`, `build:`, and uncategorized commits.
- Removed: `remove:`, `delete:`, `deprecate:`, `drop`, and similar wording.

## Files

- `changelog.sh` — generator script.
- `SAMPLE_CHANGELOG.md` — sample output from a real temporary git repository.
- `TEST_REPORT.md` — commands and validation results.
