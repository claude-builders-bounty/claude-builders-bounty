---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history with auto-categorization
trigger: generate changelog, update changelog, create changelog from commits
tools: Bash
---

# Generate Changelog

Generate or update CHANGELOG.md from the project's git history.

## When to Use

- User asks to generate or update a changelog
- User wants a summary of recent changes
- Preparing a release and need a changelog

## How to Run

1. Ensure the script exists at `skills/generate-changelog/changelog.sh` in the repo
2. Run: `bash skills/generate-changelog/changelog.sh` to generate CHANGELOG.md
3. Or run `bash skills/generate-changelog/changelog.sh --dry-run` to preview first
4. Report what categories were found and how many commits were processed

## Options

- `--dry-run` — Print to stdout instead of writing file
- `--from <tag>` — Only include commits since this tag
- `--output <file>` — Write to a different file (default: CHANGELOG.md)
