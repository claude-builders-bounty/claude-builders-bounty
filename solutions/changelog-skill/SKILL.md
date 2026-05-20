# CHANGELOG Generator Skill

You are a skilled developer tasked with generating a structured CHANGELOG.md from git history.

## Commands

- `/generate-changelog` - Generate CHANGELOG.md from git history since last tag
- `/generate-changelog <tag>` - Generate changelog up to specified tag
- `/generate-changelog <tag1>..<tag2>` - Generate changelog for tag range

## Process

1. **Fetch Git History**
   - Run `git describe --tags --abbrev=0` to get the latest tag
   - Run `git log <last-tag>..HEAD --pretty=format:"%h|%s|%an|%ad" --date=short` for commits since last tag
   - For new projects without tags, use `git log --pretty=format:"%h|%s|%an|%ad" --date=short -50`

2. **Categorize Commits**
   Analyze each commit message and categorize:
   - **Added**: New features (`feat:`, `feature:`, new functionality)
   - **Fixed**: Bug fixes (`fix:`, `bugfix:`, resolved issues)
   - **Changed**: Modifications to existing features (`change:`, `update:`, `refactor:`)
   - **Removed**: Deleted features (`remove:`, `deprecate:`)
   - **Deprecated**: Features marked for removal
   - **Security**: Security-related fixes

3. **Extract References**
   - Find issue/PR numbers: `#123`, `(#456)`
   - Group commits logically

4. **Generate Output**
   Create `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format:

   ```markdown
   # Changelog

   All notable changes to this project will be documented in this file.

   ## [Unreleased]

   ### Added
   - Brief description of added feature (#123)

   ### Fixed
   - Brief description of fix (#456)

   ## [X.Y.Z] - YYYY-MM-DD

   ### Added
   ...
   ```

## Rules

1. Use imperative mood: "Add feature" not "Added feature"
2. Include PR/issue references when available
3. Group similar changes together
4. Order categories: Added, Changed, Deprecated, Removed, Fixed, Security
5. Use ISO date format (YYYY-MM-DD)
6. Keep descriptions concise but informative
7. Don't include merge commits unless meaningful
8. Skip commits with `[skip changelog]` or `[ci skip]`

## Example Execution

```bash
# Get the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
  COMMITS=$(git log $LAST_TAG..HEAD --pretty=format:"%h|%s|%an|%ad" --date=short)
else
  COMMITS=$(git log --pretty=format:"%h|%s|%an|%ad" --date=short -50)
fi

# Parse and categorize...
```

## Output Location

Write the generated `CHANGELOG.md` to the project root directory. If a CHANGELOG.md exists, prepend new entries to it.