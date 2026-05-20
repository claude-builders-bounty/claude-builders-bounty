---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the latest tag.
---

# Generate Changelog

Use this skill when a user asks for a changelog, release notes, or a structured summary of commits.

## Workflow

1. Confirm the current directory is the target git repository.
2. Run `bash changelog.sh` from the repository root.
3. Review the generated `CHANGELOG.md` and report the output path plus any notable empty sections.

The script uses the latest git tag as the lower bound. If the repository has no tags, it uses the full commit history.
