---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

Generate a changelog from the project's git history.

Usage: `bash changelog.sh [output_file] [repo_dir]`

It will:
1. Find the last git tag
2. Collect all commits since that tag
3. Auto-categorize into: Added / Fixed / Changed / Removed
4. Write a properly formatted CHANGELOG.md

Run it at the project root:
```bash
bash changelog.sh
```
