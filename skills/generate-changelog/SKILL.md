---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history, grouped by conventional commit type and linked to GitHub commits when a GitHub remote is configured.
---

# Generate Changelog

Use this skill when the user asks to create release notes or a changelog from a repository's git history.

## Workflow

1. Run the changelog generator from the target repository root:

   ```bash
   scripts/generate-changelog.sh
   ```

2. Review `CHANGELOG.md` for any project-specific wording that should be adjusted before publishing.

3. If the release should start after a specific tag or commit, pass it explicitly:

   ```bash
   scripts/generate-changelog.sh --since v1.2.0
   ```

## Options

- `--output FILE` writes to a custom path instead of `CHANGELOG.md`.
- `--since REF` generates changes after a tag, branch, or commit.
- `--title TEXT` changes the top-level heading.

## Output

The script groups commits into:

- Breaking Changes
- Added
- Fixed
- Changed
- Removed
- Other Changes

When `remote.origin.url` points to GitHub, commit hashes and compare links are rendered as Markdown links.
