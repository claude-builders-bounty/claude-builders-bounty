# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from git history since the latest tag.

## What it does

- Finds the latest git tag and reads commits from `latest-tag..HEAD`
- Falls back to current history when no tag exists
- Groups commits into Keep-a-Changelog sections:
  - `Added`
  - `Fixed`
  - `Changed`
  - `Removed`
- Writes a formatted `CHANGELOG.md`

## Setup in 3 steps

```bash
# 1. Copy the script into any git repo
cp changelog.sh /path/to/repo/changelog.sh

# 2. Make it executable
chmod +x /path/to/repo/changelog.sh

# 3. Generate the changelog
cd /path/to/repo && ./changelog.sh
```

## Usage

```bash
./changelog.sh
./changelog.sh --output CHANGELOG.md
./changelog.sh --version 1.2.0
./changelog.sh --since v1.1.0
./changelog.sh --repo ../my-project --output ../my-project/CHANGELOG.md
```

## Classification rules

The script prefers Conventional Commits when present:

- `feat:` → `Added`
- `fix:` → `Fixed`
- `remove:`, `delete:`, `drop:`, `deprecate:` → `Removed`
- `change:`, `refactor:`, `perf:`, `chore:`, `docs:`, `test:`, `ci:`, `build:` → `Changed`

For non-conventional commits it uses conservative keyword fallback. Unknown commits go to `Changed` instead of being dropped.

## Notes

- Merge commits are skipped with `--no-merges`.
- Existing `CHANGELOG.md` is overwritten by design so CI or release scripts get deterministic output.
- No external dependencies beyond Bash, sed, date, and git.
