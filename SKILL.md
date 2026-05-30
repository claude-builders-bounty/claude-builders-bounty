# Generate Structured CHANGELOG from Git History

> A Claude Code skill that automatically generates a structured `CHANGELOG.md` from a project's git history.

## Trigger
Use `/generate-changelog` to invoke this skill.

## Instructions

When the user runs `/generate-changelog`, follow these steps:

### Step 1: Determine the Starting Point

Run the following to find the most recent git tag:

```bash
git describe --tags --abbrev=0 2>/dev/null || echo ""
```

- If a tag exists, fetch commits **since that tag**: `git log <tag>..HEAD`
- If no tag exists, fetch **all commits**: `git log`

### Step 2: Fetch and Categorize Commits

Run:

```bash
git log <range> --pretty=format:"%h|%s|%an|%ad" --date=short
```

Parse each line and categorize the commit subject into one of these categories:

| Category    | Pattern (case-insensitive prefix match)                     |
|-------------|-------------------------------------------------------------|
| **Added**   | `add`, `feat`, `new`, `introduce`, `create`, `implement`    |
| **Fixed**   | `fix`, `bug`, `patch`, `resolve`, `repair`, `hotfix`        |
| **Changed** | `change`, `update`, `update`, `refactor`, `improve`, `bump` |
| **Removed** | `remove`, `delete`, `drop`, `deprecate`, `clean`            |
| **Security**| `security`, `vuln`, `cve`, `xss`, `csrf`, `inject`          |

If no pattern matches, place the entry under **Other**.

### Step 3: Generate CHANGELOG.md

Write the output as `CHANGELOG.md` in the project root using this format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [<tag or date>] - YYYY-MM-DD

### Added
- <commit subject> (<hash>) — @<author>

### Fixed
- <commit subject> (<hash>) — @<author>

### Changed
- <commit subject> (<hash>) — @<author>

### Removed
- <commit subject> (<hash>) — @<author>

### Security
- <commit subject> (<hash>) — @<author>

### Other
- <commit subject> (<hash>) — @<author>
```

**Rules:**
- Omit any category section that has zero entries.
- Sort entries within each category by date (newest first).
- If no tag exists, use the date of the latest commit as the section header.
- Append to an existing `CHANGELOG.md` if one already exists (insert new entries at the top).

### Step 4: Show Summary

After writing the file, output a brief summary to the user:

```
✅ CHANGELOG.md generated successfully.
  - <N> commits processed since <tag or "beginning">
  - Added: <n> | Fixed: <n> | Changed: <n> | Removed: <n> | Security: <n> | Other: <n>
```

## Constraints

- This skill operates on the **local git repository** only. No remote API calls.
- It reads `git log` output directly — no third-party tools required.
- Works with any Git repository (GitHub, GitLab, Bitbucket, local).
