# Generate Changelog

Generate a structured CHANGELOG.md from git history.

## Trigger

`/generate-changelog`

## Instructions

When the user runs this command, follow these steps:

1. **Determine the version range**
   - Find the latest git tag: `git describe --tags --abbrev=0`
   - If no tags exist, use the first commit as the base
   - The version header uses the tag name or "Unreleased" if no new tag

2. **Collect commits**
   - Run: `git log <last-tag>..HEAD --pretty=format:"%s"`
   - If no previous tag: `git log --pretty=format:"%s"`

3. **Categorize commits** using conventional commit prefixes:
   - `feat:` or `feature:` → **Added**
   - `fix:` or `bugfix:` → **Fixed**
   - `refactor:`, `perf:`, `chore:`, `build:`, `ci:` → **Changed**
   - `remove:`, `deprecate:`, `revert:` → **Removed**
   - `docs:`, `test:`, `style:` → skip (omit from changelog)
   - Commits without a prefix → **Changed**

4. **Format the output**
   - Group entries under category headers in this order: Added, Fixed, Changed, Removed
   - Strip the prefix from each entry (e.g., "feat: add login" becomes "Add login")
   - Capitalize the first letter of each entry
   - Omit empty categories

5. **Write CHANGELOG.md**
   - Prepend the new version block above existing content
   - Use this format:

\`\`\`markdown
## [x.y.z] - YYYY-MM-DD

### Added
- Description of new feature

### Fixed
- Description of bug fix

### Changed
- Description of change

### Removed
- Description of removal
\`\`\`

6. **Confirm** — Show the user the generated changelog entry and ask for confirmation before writing.

## Example Output

\`\`\`markdown
## [1.2.0] - 2026-06-09

### Added
- User avatar upload endpoint
- Dark mode toggle for settings page

### Fixed
- Login redirect loop on expired tokens
- Search results pagination off-by-one error

### Changed
- Upgraded database driver to v3.2
- Rate limit increased from 100 to 200 req/min

### Removed
- Deprecated v1 API endpoints
\`\`\`

## Notes

- If the project uses `package.json`, read the version from there for the header
- If commits reference issues (e.g., "#123"), keep the reference in the entry
- Merge commits are automatically excluded by using `--no-merges` flag
