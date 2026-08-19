# SKILL.md — Auto CHANGELOG Generator

## Trigger
Use `/generate-changelog` to generate a structured CHANGELOG.md from git history since the last tag.

## Behavior

1. **Detect last tag**: Run `git describe --tags --abbrev=0 2>/dev/null` to find the most recent tag. If no tags exist, use the first commit.

2. **Fetch commits**: Run `git log <last-tag>..HEAD --pretty=format:"%H|%s|%b" --no-merges` to get all commits since the last tag.

3. **Categorize each commit** into one of these sections based on conventional-commit prefixes and keyword matching:

   | Section   | Prefixes / Keywords                              |
   |-----------|--------------------------------------------------|
   | Added     | `feat`, `add`, `new`, `introduce`, `implement`   |
   | Fixed     | `fix`, `bug`, `patch`, `resolve`, `repair`       |
   | Changed   | `change`, `update`, `improve`, `refactor`, `migrate`, `rename` |
   | Removed   | `remove`, `delete`, `drop`, `deprecate`, `revert`|
   | Security  | `security`, `vuln`, `cve`, `xss`, `injection`    |
   | Docs      | `docs`, `documentation`, `readme`, `comment`     |

   Commits that don't match any category go into **Changed**.

4. **Parse commit bodies** for breaking-change markers (`BREAKING CHANGE:`, `BREAKING:`). If found, add a **Breaking Changes** section at the top.

5. **Generate CHANGELOG.md** with this structure:

   ```markdown
   # Changelog

   ## [Unreleased] - YYYY-MM-DD

   ### Breaking Changes
   - <description from commit body>

   ### Added
   - <commit subject>

   ### Fixed
   - <commit subject>

   ### Changed
   - <commit subject>

   ### Removed
   - <commit subject>

   ### Security
   - <commit subject>

   ### Docs
   - <commit subject>
   ```

6. **Append to existing** CHANGELOG.md if it already exists (insert new entries at the top, below the header). Preserve all existing content.

7. **Commits referencing issues** (e.g. `#123`, `fixes #456`) should have the issue number linked: `[#123](../issues/123)`.

## Constraints

- Do NOT modify any source code files — only read from git history and write CHANGELOG.md.
- Do NOT delete or overwrite existing changelog sections for previous versions.
- If no commits are found since the last tag, report "No new commits since <tag>." and exit.
- Respect `.gitconfig` project conventions for `fetch.pruneTags`.

## Examples

### Input

Project with tags `v1.0.0`, `v1.1.0`. HEAD is 3 commits ahead of `v1.1.0`:

```
abc1234 feat(auth): add OAuth2 login flow
5678def fix: resolve race condition in user creation
9012ghi docs: update README with setup instructions
```

### Output

```markdown
# Changelog

## [Unreleased] - 2026-08-19

### Added
- feat(auth): add OAuth2 login flow

### Fixed
- fix: resolve race condition in user creation

### Docs
- docs: update README with setup instructions

## [v1.1.0] - ...
(preserved existing content)
```
