# Git History Changelog Generator

Generate a structured `CHANGELOG.md` from git commits since the latest tag.

## Setup and usage

1. Copy `changelog.sh` into any git repository.
2. Run `bash changelog.sh` from the repository root.
3. Commit the generated `CHANGELOG.md` after reviewing the categories.

## Behavior

- Uses `git describe --tags --abbrev=0` to find the latest tag.
- If no tag exists, it generates from the full reachable history.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed` using common commit prefixes and keywords.
- Writes a Keep-a-Changelog-style `CHANGELOG.md`.

## Example

```bash
bash changelog.sh
# Generated CHANGELOG.md from commits since v1.2.0
```

To write somewhere else:

```bash
bash changelog.sh /tmp/CHANGELOG.md
```
