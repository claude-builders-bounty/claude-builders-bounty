# SKILL: Generate Changelog

Generate a structured CHANGELOG.md from a project's git history.

## /generate-changelog

Generate a structured CHANGELOG.md from the current project's git history.

### Parameters

- `since` (optional): Only include commits since this tag (e.g., `v1.0.0`)

### Steps

1. Run `python generate_changelog.py` (or `bash changelog.sh`) in the project root
2. The script will:
   - Parse `git log` for all commits
   - Auto-detect the latest tag as a starting point
   - Categorize commits into Added/Fixed/Changed/Removed
   - Write a formatted `CHANGELOG.md`
3. Review the generated `CHANGELOG.md`
4. If any categorization looks wrong, adjust the regex in `generate_changelog.py`

### Example

```bash
# Full history
bash changelog.sh

# Since last tag only
bash changelog.sh --since v1.0.0

# Specific repo path
bash changelog.sh --repo /path/to/project
```

### Categorization Rules

| Prefix | Category |
|--------|----------|
| feat, add, new, introduce, implement | Added |
| fix, bugfix, hotfix, patch, resolve | Fixed |
| update, refactor, improve, change, chore | Changed |
| remove, delete, drop, deprecate, clean | Removed |
