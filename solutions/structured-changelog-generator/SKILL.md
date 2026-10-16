---
name: generate-changelog
description: Generate a structured CHANGELOG.md from commits since the latest Git tag.
---

# Generate Changelog

When the user invokes `/generate-changelog`:

1. Confirm the current directory is the intended Git repository.
2. Run `bash changelog.sh`. Use `--from TAG` only when the user supplies a starting tag.
3. Report the commit range and the generated file path.
4. Do not claim releases were published or tags were created; this skill only generates documentation.

The script categorizes conventional and plain commit subjects into Added, Fixed, Changed, and Removed sections and excludes merge commits.
