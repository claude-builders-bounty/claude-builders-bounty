---
name: generate-changelog
description: Generate a structured CHANGELOG.md from a git repository's commit history. Use when asked to run /generate-changelog, summarize commits since the latest tag, or produce Added/Fixed/Changed/Removed release notes from git history.
---

# Generate Changelog

Run `bash changelog.sh` from the root of a git repository to create `CHANGELOG.md` from commits since the latest tag.

Use `--since <tag-or-rev>` when the repository has no tags or when the user wants a specific release range. Use `--include-hashes` when reviewers need traceability back to exact commits.

After generation, inspect the resulting sections for obvious misclassification and adjust only if the commit text clearly indicates a better category.
