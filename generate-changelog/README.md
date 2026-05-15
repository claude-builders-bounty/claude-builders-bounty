# Generate Changelog Skill

Create a structured `CHANGELOG.md` from git history.

## Setup

1. Copy `SKILL.md` and `scripts/changelog.sh` into your Claude Code skill folder, or keep this directory in a repo.
2. From the target repo root, run `bash path/to/scripts/changelog.sh`.
3. Review the generated `CHANGELOG.md` and commit it.

## Usage

```bash
bash scripts/changelog.sh
bash scripts/changelog.sh --version v1.2.0 --from v1.1.0 --to HEAD
bash scripts/changelog.sh --dry-run --output RELEASE_NOTES.md
```

The script fetches commits since the latest git tag by default and groups entries into `Added`, `Fixed`, `Changed`, and `Removed`.
