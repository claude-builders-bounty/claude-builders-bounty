# Generate Changelog

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup / usage

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh`.
3. Review the generated `CHANGELOG.md`.

## What it does

- Detects the latest git tag and reads commits from `latest-tag..HEAD`.
- Falls back to all commits when the repo has no tags.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed` using Conventional Commit prefixes and common keywords.
- Writes a Keep-a-Changelog-style `CHANGELOG.md` with commit hashes for traceability.

## Optional flags

```bash
bash changelog.sh --output RELEASE_NOTES.md
bash changelog.sh --from v1.2.3
bash changelog.sh --title "Unreleased"
```
