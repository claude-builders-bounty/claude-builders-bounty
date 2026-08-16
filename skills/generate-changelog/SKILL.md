---
name: generate-changelog
description: >-
  Use this skill when the user asks to generate a changelog, create a changelog from git history, or summarize recent commits.
---

# Generate Changelog Skill

This skill automatically generates a formatted `CHANGELOG.md` file based on the git history since the last tag.

## Steps

1. Run the `changelog.sh` script to parse git history and categorize commits:
   `bash changelog.sh`
   (Note: If `changelog.sh` is not in the root, it may be in `skills/generate-changelog/scripts/changelog.sh`).
2. The script will output a file named `CHANGELOG.md` in the current working directory.
3. Review the generated `CHANGELOG.md` file using `cat CHANGELOG.md` to ensure it matches expectations.
4. Inform the user that the changelog has been successfully generated.
