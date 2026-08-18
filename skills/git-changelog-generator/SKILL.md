---
name: git-changelog-generator
description: Generate a structured Keep-a-Changelog formatted CHANGELOG.md from git history since the latest tag or commit.
version: 1.0.0
triggers:
  - "/generate-changelog"
  - "generate changelog"
  - "update changelog"
---

# Git Changelog Generator Skill

Automatically inspects the local Git commit history, categorizes commits into Conventional Commit buckets (`Added`, `Fixed`, `Changed`, `Removed`, `Security`, `Documentation`), and generates or updates a clean, markdown-compliant `CHANGELOG.md`.

## Instructions for Agent

When the user triggers `/generate-changelog` or asks to document recent changes:

1. Identify the latest git tag using `git tag --sort=-creatordate`. If none exists, read from initial commit.
2. Execute the bundled generator script:
   ```bash
   python3 skills/git-changelog-generator/generate_changelog.py --version "1.0.0" --output "CHANGELOG.md" --prepend
   ```
3. Verify that the generated `CHANGELOG.md` reflects all recent changes accurately.
4. Present a summary of the changelog to the user.

## Command Line Options

- `--version <name>`: Release version header (e.g. `1.0.0` or `Unreleased`).
- `--since <tag>`: Compare commits starting from this tag or commit hash.
- `--output <path>`: Destination path for the markdown file (default: `CHANGELOG.md`).
- `--prepend`: Prepend the new release section to the top of existing `CHANGELOG.md`.
- `--stdout`: Print output to console without writing to disk.
