# Generate Changelog

Create a categorized `CHANGELOG.md` from Git commits made after the latest tag.

## Setup and use

1. Copy this folder into the repository that needs release notes.
2. From that repository's root, run `python scripts/generate_changelog.py`.
3. Review and commit the generated `CHANGELOG.md`.

Use `--since v1.2.0` to choose a tag or `--output docs/CHANGELOG.md` to change the target file.

## Verified sample

`sample-output.md` was generated from the public [`pallets/itsdangerous`](https://github.com/pallets/itsdangerous) repository using commits after tag `2.1.1`.
