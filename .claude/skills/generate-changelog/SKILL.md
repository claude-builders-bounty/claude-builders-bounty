---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history. Use when the user asks for release notes, a changelog, or categorized changes since the latest tag.
tools: Bash
---

# Generate Changelog

1. Confirm the current directory is inside the target git repository.
2. Run `bash changelog.sh [output_file]`.
3. Review uncategorized commit subjects and the `Breaking Changes` section.
4. Report the selected git range and output path.

The script uses the latest reachable tag as the starting point, preserves commit subjects containing delimiters, and groups conventional commits into Breaking Changes, Added, Fixed, Changed, and Removed.

Do not invent release notes that are not supported by git history. If commit messages are ambiguous, leave them in Changed and tell the user what needs manual review.
