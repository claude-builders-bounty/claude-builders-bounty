# Generate Changelog Skill

## Description
Automatically generates a structured `CHANGELOG.md` from the project's git history using conventional commit prefixes.

## Trigger
`/generate-changelog`

## Instructions

When the user invokes `/generate-changelog`, follow these steps:

### 1. Detect Git Context
- Verify the current directory is a git repository
- Find the latest git tag: `git describe --tags --abbrev=0`
- If no tag exists, use all commits

### 2. Gather Commits
Run this command to get structured commit data since the last tag:

```bash
git log $(git describe --tags --abbrev=0 2>/dev/null && echo '..HEAD' || true) \
  --pretty=format:'%s|||%h|||%an|||%ad' --date=short
```

If no tags exist, omit the range to get all commits.

### 3. Categorize Commits
Parse each commit subject line and assign to one of four categories:

| Category  | Matching prefixes (case-insensitive)                          |
|-----------|---------------------------------------------------------------|
| **Added** | `feat`, `add`, `new`, `introduce`                            |
| **Fixed** | `fix`, `bugfix`, `patch`, `hotfix`                            |
| **Changed** | `change`, `refactor`, `docs`, `perf`, `style`, `chore`, `ci`, `test`, `build`, `update`, `improve` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate`                     |

**Rules:**
- Strip conventional commit prefixes (e.g., `feat(auth):` → just the description)
- Strip parenthetical scopes
- If no prefix matches, use keyword fallback on the full message
- Commits with no match default to **Changed**
- Skip merge commits (`Merge branch ...`)

### 4. Format the Output
Generate a `CHANGELOG.md` in this exact format:

```markdown
# Changelog

## [Unreleased] — YYYY-MM-DD

_Range: Since vX.Y.Z_ (or "All history" if no tags)

### Added
- Description of new feature (`abc1234`) — Author Name 2025-01-15

### Fixed
- Description of fix (`def5678`) — Author Name 2025-01-14

### Changed
- Description of change (`ghi9012`) — Author Name 2025-01-13

### Removed
- Description of removal (`jkl3456`) — Author Name 2025-01-12
```

**Formatting rules:**
- Each entry: `- Description (\`short-hash\`) — Author YYYY-MM-DD`
- Only include categories that have entries
- Empty categories are omitted
- Entries are listed newest-first within each category

### 5. Write the File
- Default output: `CHANGELOG.md` in the repo root
- If the user specifies a path, use that instead
- If `CHANGELOG.md` already exists, prepend the new content after the `# Changelog` heading (preserve older entries below a `---` separator)

### 6. Confirm
Report to the user:
- Number of commits processed
- Number of entries per category
- File path where the changelog was written

## Alternative: Standalone Script

If the user prefers, they can run the bash script directly:

```bash
bash changelog.sh                    # Default: CHANGELOG.md, since last tag
bash changelog.sh -o NOTES.md       # Custom output file
bash changelog.sh --tag v1.0.0       # Since specific tag
bash changelog.sh --all              # All history
```

## Edge Cases
- **No commits since tag**: Inform the user and exit cleanly
- **No git repo**: Show an error message
- **Dirty working tree**: Proceed normally (no stash needed)
- **Shallow clones**: `git log` may have limited history; warn if fewer than expected commits
