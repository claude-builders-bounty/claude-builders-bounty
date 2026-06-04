---
name: generate-changelog
description: Generate a structured CHANGELOG from git history
---

<objective>
Generate a structured CHANGELOG.md file from the git history of the current repository, automatically categorizing changes into Added, Fixed, Changed, and Removed categories.
</objective>

<process>
1. Run the Python generation utility:
   ```bash
   python generate_changelog.py
   ```
2. Verify that the `CHANGELOG.md` file has been created or updated in the repository root.
</process>

<notes>
- Requires python3 to be installed.
- Requires the repository to be initialized with Git.
- Auto-detects the last tag using `git describe` to query only commits since the last release.
</notes>
