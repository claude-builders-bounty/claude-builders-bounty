---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commits since the latest tag.
---

# Generate Changelog

Use this skill when a user asks for `/generate-changelog`, a release changelog, or a structured `CHANGELOG.md` from git history.

## Workflow

1. Run `bash changelog.sh` from the repository root.
2. Review the generated `CHANGELOG.md` for category fit and obvious duplicate entries.
3. If the project uses custom commit conventions, adjust the category wording without changing the four required sections: `Added`, `Fixed`, `Changed`, and `Removed`.

The script fetches tags when an `origin` remote exists, finds the latest tag with `git describe --tags --abbrev=0`, scans commits after that tag, and writes the changelog.
