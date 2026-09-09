# Git history CHANGELOG generator

`changelog.sh` turns commits since the most recent Git tag into a structured `CHANGELOG.md`. It groups conventional commit prefixes and common action words under `Added`, `Fixed`, `Changed`, and `Removed`.

## Setup and use

1. Copy `changelog.sh` into the root of a Git repository and make it executable: `chmod +x changelog.sh`.
2. Create a release tag when the next changelog should start a new section: `git tag v1.0.0`.
3. Run `bash changelog.sh` (or `./changelog.sh`) to write `CHANGELOG.md`.

The script includes every commit after the latest tag; with no tags, it includes the repository's complete history. Use `-o PATH` to choose another output file, for example `bash changelog.sh -o docs/CHANGELOG.md`. Existing output is replaced atomically after the Git history has been read successfully.

## Generated format

Each run writes a heading with the latest tag (or `Unreleased`), the generation date, and all four categories. Commits that do not match a more specific prefix are placed in `Changed`. The commit's short ID is included so each entry can be traced back to Git history.

## Validation

The script was run against the real GitHub repository [claude-builders-bounty/claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty). The resulting sample is checked in as [`CHANGELOG.md`](CHANGELOG.md).
