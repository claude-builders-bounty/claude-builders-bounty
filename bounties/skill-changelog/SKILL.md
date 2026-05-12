# Skill: Generate Structured CHANGELOG From Git History

## Description
Generate a `CHANGELOG.md` entry from the repository's git history using the Keep a Changelog format. Use this skill when the user runs `/generate-changelog` or asks Claude Code to generate a changelog.

## Process

1. Determine the commit range:
   - Default to commits since the most recent git tag.
   - If the repository has no tags, use the last 20 commits.
   - Respect explicit user scopes such as "last N commits", "since DATE", or "between tag A and tag B".

2. Fetch the commit history:
   ```bash
   latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
   if [ -n "$latest_tag" ]; then
     git log "${latest_tag}..HEAD" --format="%H|%s|%an|%ad" --date=short
   else
     git log -20 --format="%H|%s|%an|%ad" --date=short
   fi
   ```

3. Categorize commits by conventional commit prefix:
   - `feat:` or `feature:` -> `Added`
   - `fix:` or `bugfix:` -> `Fixed`
   - `docs:` or `doc:` -> include only if user-facing
   - `refactor:`, `perf:`, `performance:`, `deps:`, or `dep:` -> `Changed`
   - `remove:` or `removed:` -> `Removed`
   - `security:` or `sec:` -> `Security`
   - No prefix -> use judgment, usually `Changed`

4. Skip commits that should not appear in a user-facing changelog:
   - Merge commits
   - Test-only changes
   - CI-only changes
   - Formatting-only changes
   - WIP or temporary commits

5. Write the changelog entry:
   - Use `## [Unreleased] - YYYY-MM-DD` unless the user provides a release version.
   - Include only non-empty sections.
   - Order sections as `Added`, `Changed`, `Fixed`, `Removed`.
   - Write each entry as one concise bullet without a trailing period.
   - Include PR or issue numbers when visible in the commit subject.
   - Combine related commits into one changelog bullet.
   - Do not invent changes that are not supported by the git log.

## Output Format

```markdown
## [Unreleased] - YYYY-MM-DD

### Added
- Added OAuth sign-in support (#142)

### Changed
- Improved dashboard export performance (#144)

### Fixed
- Fixed timezone handling in scheduled reports (#139)

### Removed
- Removed deprecated legacy formatter
```

## Updating CHANGELOG.md
If `CHANGELOG.md` exists, insert the new entry after the title/header. If it does not exist, create it with this structure:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - YYYY-MM-DD
```
