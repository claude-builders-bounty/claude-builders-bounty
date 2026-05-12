---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when a repository needs a release-ready `CHANGELOG.md`
generated from local git history.

## Command

Run:

```bash
bash skills/generate-changelog/changelog.sh
```

The script inspects commits since the latest git tag. If the repository has no
tags, it uses the full commit history.

## Output

The script writes `CHANGELOG.md` at the repository root with these sections:

- Added
- Fixed
- Changed
- Removed

Each commit is categorized from its subject line. Conventional Commit prefixes
such as `feat:`, `fix:`, `refactor:`, `docs:`, and `remove:` are recognized,
with sensible keyword fallbacks for non-conventional histories.

## Notes

- The script must be run from anywhere inside a git repository.
- Merge commits are ignored to keep the changelog focused on authored changes.
- Existing `CHANGELOG.md` content is replaced by the newly generated output.
