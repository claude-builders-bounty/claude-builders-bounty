---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history since the last tag
---

# Generate Changelog

You are a changelog generator. When the user invokes `/generate-changelog`, analyze the git history of the current repository and produce a well-structured CHANGELOG.md.

## Steps

1. **Find the last git tag** by running:
   ```
   git describe --tags --abbrev=0 2>/dev/null
   ```
   If no tag exists, use the entire commit history.

2. **Fetch all commits since that tag** by running:
   ```
   git log <last-tag>..HEAD --pretty=format:"%s|%h|%ad" --date=short
   ```
   If no tag was found, run:
   ```
   git log --pretty=format:"%s|%h|%ad" --date=short
   ```

3. **Categorize each commit** by its conventional commit prefix or keywords:

   | Category    | Matching prefixes / keywords                          |
   |-------------|-------------------------------------------------------|
   | Added       | `feat`, `add`, `new`, `introduce`, `implement`        |
   | Fixed       | `fix`, `bugfix`, `patch`, `resolve`, `correct`        |
   | Changed     | `refactor`, `change`, `update`, `improve`, `enhance`  |
   | Removed     | `remove`, `delete`, `drop`, `deprecate`, `revert`     |
   | Other       | Anything that does not match the above categories      |

   Match case-insensitively against the beginning of the commit subject. For example:
   - `feat: add user auth` -> Added
   - `fix(api): resolve timeout` -> Fixed
   - `update README` -> Changed
   - `remove legacy endpoint` -> Removed

4. **Determine the version header**:
   - If a tag exists, label the section as `[Unreleased]` (changes since that tag).
   - If no tags exist, label it `[0.1.0]` with today's date.
   - Use the format: `## [Version] - YYYY-MM-DD`

5. **Output the CHANGELOG.md** in this exact format:

   ```markdown
   # Changelog

   All notable changes to this project will be documented in this file.

   The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

   ## [Version] - YYYY-MM-DD

   ### Added
   - Description of added feature (hash)

   ### Fixed
   - Description of fix (hash)

   ### Changed
   - Description of change (hash)

   ### Removed
   - Description of removal (hash)
   ```

   - Omit any category section that has zero entries.
   - Strip the conventional commit prefix from the description (e.g., `feat: add auth` becomes `Add auth`).
   - Capitalize the first letter of each entry.
   - Include the short commit hash in parentheses at the end of each line.

6. **Write the file** to `CHANGELOG.md` in the repository root.

7. **Report** the result to the user, showing:
   - How many commits were processed
   - How many entries per category
   - The path to the generated file

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - 2026-03-31

### Added
- User authentication with OAuth2 (a1b2c3d)
- Rate limiting middleware (e4f5g6h)

### Fixed
- Token refresh loop on expired sessions (i7j8k9l)

### Changed
- Upgrade dependencies to latest versions (m0n1o2p)
```
