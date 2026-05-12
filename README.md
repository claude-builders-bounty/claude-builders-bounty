# Git changelog generator

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Install and run

```bash
cp scripts/changelog.sh /path/to/repo/scripts/changelog.sh
bash scripts/changelog.sh
```

Optional custom output path:

```bash
bash scripts/changelog.sh docs/CHANGELOG.md
```

## What it does

- detects the latest git tag with `git describe --tags --abbrev=0`
- reads commits from `latest-tag..HEAD`
- falls back to all history when no tag exists
- categorizes commit subjects into:
  - `Added`
  - `Fixed`
  - `Changed`
  - `Removed`
- writes a formatted changelog file

## Categorization rules

The script uses simple commit-subject prefixes and keywords:

- `feat:`, `add:`, `feature:` → Added
- `fix:`, `bugfix:` → Fixed
- `refactor:`, `update:`, `change:` → Changed
- `remove:`, `delete:` → Removed
- unknown subjects → Changed

## Sample output

See `examples/changelog-generator/CHANGELOG.sample.md` for output generated from this repository.
