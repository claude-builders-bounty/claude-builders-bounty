---
name: generate_changelog
description: Generates a structured CHANGELOG.md file based on git history since the last tag.
---

# Generate Changelog Skill

This skill allows you to automatically generate a formatted `CHANGELOG.md` file for the project.
It analyzes git history since the last git tag (or all commits if no tag exists), categorizes them into Added, Fixed, Changed, and Removed, and produces a markdown file.

## Instructions

When the user asks to generate a changelog, create a changelog, or summarize recent commits:
1. Run the `changelog.sh` script provided in this skill directory using bash:
   ```bash
   bash .claude/skills/generate-changelog/changelog.sh
   ```
2. The script will output a file named `CHANGELOG.md` in the current working directory.
3. Review the generated `CHANGELOG.md` file to ensure it matches the user's expectations.
4. Let the user know the changelog has been generated.
