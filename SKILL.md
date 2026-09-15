---
name: generate-changelog
description: Generates a CHANGELOG.md file from git commit history based on conventional commits.
---

# Generate Changelog Skill

This skill automatically generates a `CHANGELOG.md` file by categorizing git commit history since the last git tag (or all commits if no tags exist).

## Usage
Run the following script wrapper to generate the changelog:
`./changelog.sh`

The script will:
1. Find the most recent git tag.
2. Fetch commits since the tag (or all commits if none).
3. Categorize them into `Added`, `Fixed`, `Changed`, `Removed`, or `Other`.
4. Output a `CHANGELOG.md` file in the current directory.
