---
name: changelog-generator
description: Generate a structured CHANGELOG from git history
---

# Changelog Generator Skill

This skill allows Claude to automatically generate a structured `CHANGELOG.md` file from your project's git history.

## How to trigger
User can type `/generate-changelog` or ask "generate a changelog".

## Instructions
1. Run the `changelog.sh` script located in `skills/changelog-generator/changelog.sh`.
   Ensure it has executable permissions (`chmod +x skills/changelog-generator/changelog.sh`).
2. Alternatively, you can run `bash skills/changelog-generator/changelog.sh`.
3. If the script succeeds, a `CHANGELOG.md` will be created or updated in the current working directory.
4. Output the results or summary to the user.
