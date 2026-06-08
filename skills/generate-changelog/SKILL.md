---
name: generate-changelog
description: Generate a structured CHANGELOG.md from the current repository's git history since the latest tag.
---

# Generate Changelog

Use this skill when the user asks for `/generate-changelog`, wants a release
draft, or needs `CHANGELOG.md` regenerated from commit history.

## Workflow

1. Run `bash changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md` and move any ambiguous commit from
   `Changed` into a more precise category if the commit subject makes that safe.
3. Report the detected tag range and the output path.

## Categorization Rules

- `feat`, `add`, `create`, and `initial` commits go to `Added`.
- `fix`, `bug`, `patch`, `hotfix`, and `repair` commits go to `Fixed`.
- `remove`, `delete`, `drop`, and `deprecate` commits go to `Removed`.
- Everything else goes to `Changed` so the changelog remains complete.

## Output Contract

The generated changelog must include:

- `# Changelog`
- `## Unreleased - YYYY-MM-DD`
- `Added`, `Fixed`, `Changed`, and `Removed` sections
- commit subject, short hash, author, and commit date for each entry

If the repository has no git tags, the script uses the full reachable history.
If tags exist, it uses commits after the latest tag.
