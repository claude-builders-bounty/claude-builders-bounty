---
name: /generate-changelog
description: Generate a structured CHANGELOG.md from git history, categorized by conventional commit types (Added / Fixed / Changed / Removed). Use this whenever the user asks to generate a changelog, runs /generate-changelog, or asks to document recent changes.
---

# /generate-changelog Skill

This skill generates a structured `CHANGELOG.md` from the project's git history using conventional commit prefixes.

## When to Use

- User runs `/generate-changelog`
- User asks to generate a changelog
- User asks to document recent changes

## How It Works

1. **Find the latest tag** with `git describe --tags --abbrev=0`
2. **Fetch commits** since that tag with `git log <tag>..HEAD --pretty=format:"%s"`
3. **Categorize commits** by conventional commit prefix:
   - `feat` → **Added**
   - `fix` → **Fixed**
   - `refactor`, `docs`, `chore`, `style`, `perf`, `build`, `ci`, `test` → **Changed**
   - `revert`, `breaking` → **Removed**
   - Everything else → **Other**
4. **Write** a properly formatted `CHANGELOG.md` to the repository root

## Output Format

```markdown
# Changelog

## v1.2.0 — 2025-01-15

### Added

- feat(auth): add OAuth2 login support
- feat(api): introduce GraphQL endpoint

### Fixed

- fix(core): resolve null pointer in parser
- fix(ui): correct button alignment on mobile

### Changed

- refactor(utils): simplify date formatting logic
- docs(readme): update installation instructions

### Removed

- chore(deps): drop deprecated lodash dependency

### Other

- ci: update GitHub Actions workflow
```

## Fallback

If no git tags exist, generate a changelog from **all** commits in history.

## Verification

After generation, confirm:
- `CHANGELOG.md` exists and is non-empty
- Commits are correctly categorized
- Date format is `YYYY-MM-DD`
- The output is valid markdown

## Notes

- Always run `git log` to inspect raw commits before categorizing
- If the repo has no `.git`, inform the user
