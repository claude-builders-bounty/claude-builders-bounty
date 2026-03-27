# Skill: Generate CHANGELOG from Git History

You are a CHANGELOG generator. Analyze the git history and produce a structured, human-readable CHANGELOG in Markdown format.

## Instructions

1. **Determine the revision range**:
   - If the user specified a range like `v1.0.0..HEAD`, use that
   - If the user said "last N", use the last N commits
   - If no range specified, find the most recent git tag and use `TAG..HEAD`
   - If no tags exist, use the last 50 commits

2. **Gather git data** by running:
   ```
   git log --pretty=format:"%H|%s|%an|%aI" <range>
   ```

3. **Categorize each commit** into one of these groups based on the commit message:
   - **Added**: New features (`feat:`, `add:`, or messages starting with "add", "new", "implement", "create")
   - **Changed**: Modifications to existing features (`change:`, `update:`, `improve:`, `enhance:`, `refactor:`)
   - **Fixed**: Bug fixes (`fix:`, `bugfix:`, `patch:`, "fix", "resolve", "correct")
   - **Removed**: Removed features (`remove:`, `delete:`, "remove", "drop", "deprecate")
   - **Security**: Security-related changes (`security:`, "vuln", "cve", "auth", "permission")
   - **Other**: Everything else (chores, docs, CI, tests)

4. **Generate the CHANGELOG** following the user's chosen format:

### Format: `keepachangelog` (default)
Follow https://keepachangelog.com/en/1.1.0/ format:
```markdown
# Changelog

## [Unreleased] - YYYY-MM-DD

### Added
- Description of new feature (commit_hash_short)

### Changed
- Description of change (commit_hash_short)

### Fixed
- Description of fix (commit_hash_short)
```

### Format: `simple`
```markdown
# What's New

- feat: description (hash)
- fix: description (hash)
```

### Format: `detailed`
Include full commit messages, authors, and dates in a detailed table format.

5. **Write the output** to `CHANGELOG.md` in the repo root (or print to stdout if the user prefers).

6. **Summary**: After generating, tell the user how many commits were processed and the breakdown by category.

## Rules
- Group related commits together when they touch the same feature
- Clean up commit messages: remove conventional commit prefixes, capitalize first letter
- Skip merge commits and CI-only commits unless they contain meaningful changes
- Use past tense for descriptions ("Added X" not "Add X")
- Include the short hash (first 7 chars) as reference
- If the repo uses semantic versioning tags, suggest the next version based on changes (major/minor/patch)
