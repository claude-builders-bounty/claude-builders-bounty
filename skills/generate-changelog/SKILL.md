---
name: generate-changelog
description: Automatically generates or updates a structured Keep a Changelog CHANGELOG.md from git history since the latest tag or initial commit.
commands:
  - /generate-changelog
---

# Generate Changelog Skill

You are an expert technical release manager adhering strictly to the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/) specifications.

When the user runs `/generate-changelog` or asks to generate a changelog:

1. **Inspect Git Tags**:
   - Run `git describe --tags --abbrev=0` to identify the most recent release tag.
   - If no tags exist, inspect all commits since the repository root (`git rev-list --max-parents=0 HEAD`).

2. **Collect Commit Logs**:
   - Run `git log <last-tag>..HEAD --pretty=format:"%h%x09%s%x09%an%x09%ad" --date=short` to retrieve commits.

3. **Categorize Commits**:
   Map conventional commit prefixes and semantic keywords into canonical categories:
   - **`Added`**: `feat:`, `feat(...)`, `add`, `new`, `implement`, `support`
   - **`Fixed`**: `fix:`, `fix(...)`, `bug`, `patch`, `resolve`, `close`
   - **`Changed`**: `refactor:`, `perf:`, `chore:`, `style:`, `update`, `optimize`
   - **`Removed`**: `remove`, `delete`, `deprecate`, `drop`
   - **`Security`**: `sec:`, `security`, `cve`, `vulnerability`, `sanitize`

4. **Format Markdown Output**:
   Structure the new release block with current date `[YYYY-MM-DD]`:
   ```markdown
   ## [Unreleased] - YYYY-MM-DD

   ### Added
   - Description of new feature ([hash](commit-url))

   ### Fixed
   - Description of bug fix ([hash](commit-url))

   ### Changed
   - Description of internal change ([hash](commit-url))

   ### Removed
   - Description of removed capability ([hash](commit-url))
   ```

5. **Update or Prepend `CHANGELOG.md`**:
   - If `CHANGELOG.md` exists, prepend the new release block directly beneath the preamble without overwriting historical release notes.
   - If `CHANGELOG.md` does not exist, initialize it with the standard Keep a Changelog header.
