# Git Changelog Generator

`changelog.sh` generates a structured `CHANGELOG.md` from git history.

It looks for the latest git tag and categorizes commits since that tag into:

- Added
- Fixed
- Changed
- Removed

If the repository has no tags, it uses the available history.

## Setup and usage in 3 steps

```bash
chmod +x changelog.sh
./changelog.sh
cat CHANGELOG.md
```

Optional output path:

```bash
./changelog.sh docs/CHANGELOG.md
```

## Categorization rules

The script uses commit subject prefixes and keywords:

- `feat:`, `feature:`, `add:` → Added
- `fix:`, `bug:`, `hotfix:` → Fixed
- `remove:`, `delete:`, `drop` → Removed
- `refactor:`, `chore:`, `docs:`, `test:`, `ci:`, `update:` → Changed

Unknown subjects are placed under `Changed` so no commit is lost.

## Sample output

A real sample generated from this repository is included at:

```text
samples/CHANGELOG.sample.md
```

## Test

Run the included smoke test to verify latest-tag range detection and all four output categories:

```bash
bash tests/test_changelog.sh
```
