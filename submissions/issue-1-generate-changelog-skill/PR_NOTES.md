# PR Notes

Closes #1.

## What Changed

- Added a native `generate-changelog` Claude Code skill with `SKILL.md`.
- Added a deterministic Python script for generating `CHANGELOG.md` from commits since the latest git tag.
- Added `changelog.sh` as the bash command path.
- Added tests and a sample output generated from a real public GitHub repository.

## Acceptance Criteria

- Works via `bash changelog.sh`.
- Fetches commits since the latest git tag.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Outputs formatted `CHANGELOG.md`.
- Includes a sample generated from `pallets/markupsafe`.
- README setup is three steps or fewer.
