# Generate Changelog

Generate a structured `CHANGELOG.md` from the current repository's git history.

## Setup (3 steps)

1. Copy `changelog.sh` into the root of any git repository.
2. Run `chmod +x changelog.sh` once.
3. Run `./changelog.sh` or `bash changelog.sh` to write `CHANGELOG.md`.

## What it does

- Detects the latest git tag and reads commits from that tag to `HEAD`.
- Falls back to the full repository history when no tag exists.
- Ignores merge commits to keep the output focused.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed` using common Conventional Commit prefixes and plain-English prefixes.
- Writes a Keep-a-Changelog-style Markdown file.

## Optional output path

Pass a file path to write somewhere other than `CHANGELOG.md`:

```bash
bash changelog.sh docs/CHANGELOG.md
```
