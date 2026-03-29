---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from git commit history since the last tag.

## Steps

1. **Find the last git tag** by running:
   ```bash
   git describe --tags --abbrev=0 2>/dev/null || echo ""
   ```

2. **Get all commits since that tag** (or all commits if no tag exists):
   - If a tag was found, run: `git log <tag>..HEAD --pretty=format:"%s" --no-merges`
   - If no tag, run: `git log --pretty=format:"%s" --no-merges`
   Also get the tag name and today's date for the header.

3. **Categorize each commit** into one of four sections based on the commit message:
   - **Added**: commits starting with `feat`, `add`, `new`, `create`, `implement`, `introduce`, or containing "add support"
   - **Fixed**: commits starting with `fix`, `bug`, `patch`, `resolve`, `correct`, `repair`, or containing "hotfix"
   - **Changed**: commits starting with `refactor`, `update`, `improve`, `enhance`, `modify`, `change`, `rename`, `move`, `migrate`, `perf`, `optimize`, `style`, `chore`, `build`, `ci`, `docs`
   - **Removed**: commits starting with `remove`, `delete`, `drop`, `deprecate`, `revert`

   If a commit doesn't match any pattern, put it under **Changed**.

4. **Write the CHANGELOG.md** file with this format:

   ```markdown
   # Changelog

   ## [Unreleased] - YYYY-MM-DD

   ### Added
   - commit message 1
   - commit message 2

   ### Fixed
   - commit message 3

   ### Changed
   - commit message 4

   ### Removed
   - commit message 5
   ```

   Rules:
   - Use the current date in YYYY-MM-DD format
   - If a tag exists, use `[vX.Y.Z → Unreleased]` as the version header
   - Only include sections that have commits (skip empty sections)
   - Strip conventional commit prefixes (e.g., `feat: add login` becomes `add login`, `fix(auth): token bug` becomes `token bug`)
   - Capitalize the first letter of each entry
   - If a `CHANGELOG.md` already exists, prepend the new section after the `# Changelog` header, preserving previous entries

5. **Report** the result: how many commits were categorized, which sections were populated, and the output file path.
