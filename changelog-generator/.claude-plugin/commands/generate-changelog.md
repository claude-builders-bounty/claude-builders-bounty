---
description: Generates a structured CHANGELOG.md from git history since the last tag.
allowed-tools: [Bash, FileEdit]
---

You are an expert release manager. Generate a structured `CHANGELOG.md` file from the project's git history.

1. **Find the reference point:**
   - Run `git describe --tags --abbrev=0` to get the last tag.
   - If that fails (no tags exist), run `git rev-list --max-parents=0 HEAD` to get the first commit.

2. **Fetch commits:**
   - Fetch commit messages from that reference to HEAD.
   - Use: `git log <reference>..HEAD --pretty=format:"- %h %s" --no-merges`
   - If there are no tags, use: `git log --pretty=format:"- %h %s" --no-merges`

3. **Categorize the commits semantically:**
   - Analyze each commit message and categorize it into EXACTLY ONE of these categories based on its intent:
     * `Added`: New features, capabilities, or additions.
     * `Fixed`: Bug fixes, hotfixes, or corrections.
     * `Changed`: Refactoring, updates, formatting, or improvements.
     * `Removed`: Deletions, deprecations, or drops.
   - DO NOT invent any new categories.

4. **Format the Changelog:**
   - Group the categorized commits. Omit any category that has no commits.
   - Output format must strictly match:
     