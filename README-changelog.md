# Git Changelog Generator

`changelog.sh` generates a structured `CHANGELOG.md` from git history since the latest tag.

## Setup in 3 steps

```bash
chmod +x changelog.sh
./changelog.sh
cat CHANGELOG.md
```

## What it does

- Detects the latest git tag with `git describe --tags --abbrev=0`.
- Uses commits since that tag, or all commits if the repo has no tags.
- Skips merge commits.
- Auto-categorizes commit subjects into:
  - Added
  - Fixed
  - Changed
  - Removed
- Writes a Markdown changelog with short commit hashes.

## Usage

Default output:

```bash
./changelog.sh
```

Custom output file:

```bash
./changelog.sh RELEASE_NOTES.md
```

## Categorization rules

- `feat:`, `feature:`, `add:` → Added
- `fix:`, `bugfix:`, `hotfix:` → Fixed
- `remove:`, `delete:` → Removed
- `change:`, `refactor:`, `perf:`, `docs:`, `test:`, `chore:`, `build:`, `ci:` → Changed
- Unknown prefixes default to Changed

## Safety

The script only reads git history and writes the requested changelog file. It does not modify commits, tags, branches, or remotes.
