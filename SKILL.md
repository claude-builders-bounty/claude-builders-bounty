---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a repository's git history.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, release notes, or a structured changelog from git commits.

## Workflow

1. Confirm the current directory is the git repository to summarize, or ask for the repository path.
2. Run `bash changelog.sh [repo-path] [output-file]`.
3. Review the generated `CHANGELOG.md` and adjust any category that needs human judgment before publishing.

## Behavior

The script reads commits since the latest git tag. If the repository has no tags, it reads the full commit history. It categorizes commits into:

- `Added`
- `Fixed`
- `Changed`
- `Removed`

The generated changelog includes commit subjects and short hashes so reviewers can trace every entry.
