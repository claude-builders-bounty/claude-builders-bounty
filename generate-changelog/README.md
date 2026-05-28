# Generate Changelog

Create a structured `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy `changelog.sh` into the root of any git repository.
2. Run `bash changelog.sh` or `bash changelog.sh v1.2.3` to override the base tag.
3. Commit the generated `CHANGELOG.md`.

## What It Does

- Finds commits since the latest reachable tag, or all commits when no tag exists.
- Categorizes commits into `Added`, `Fixed`, `Changed`, and `Removed`.
- Writes a Keep a Changelog-style Markdown file with commit hashes for traceability.

