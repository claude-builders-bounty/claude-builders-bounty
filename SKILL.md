---
name: generate-changelog
description: Automatically generates a structured CHANGELOG.md from git history categorized into Added, Fixed, Changed, and Removed.
user-facing: true
---

# Generate Changelog Skill

This skill parses git commit history since the last git tag (or all commits if no tag exists) and compiles a clean, standardized `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/).

## Usage

Run the `/generate-changelog` command or execute `bash changelog.sh`:

```bash
# Basic usage — generates CHANGELOG.md in current project
bash changelog.sh

# Specify output file
bash changelog.sh -o RELEASES.md

# Generate since a specific tag
bash changelog.sh --since v1.0.0

# Output directly to stdout
bash changelog.sh --stdout
```

## How It Works

1. Identifies the latest git tag using `git describe --tags --abbrev=0`.
2. Collects commits from `git log` since that tag.
3. Automatically classifies each commit using Conventional Commit prefixes and keywords:
   - **Added**: `feat:`, `add:`, `new:`
   - **Fixed**: `fix:`, `bug:`, `patch:`, `resolve:`
   - **Changed**: `refactor:`, `chore:`, `update:`, `docs:`
   - **Removed**: `remove:`, `delete:`, `deprecate:`
4. Formats clean bullet points with commit hash and author details.
5. Writes the result to `CHANGELOG.md`.
