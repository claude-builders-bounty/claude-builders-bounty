---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a repository needs a release-ready changelog generated from git commits.

## Command

Run:

```bash
bash changelog.sh
```

On Windows without Bash, run:

```bash
python generate_changelog.py
```

The script finds the latest git tag and groups non-merge commits since that tag into:

- Added
- Fixed
- Changed
- Removed

If the repository has no tags, it uses the full commit history. Pass an optional output path to write somewhere other than `CHANGELOG.md`:

```bash
bash changelog.sh docs/CHANGELOG.md
```
