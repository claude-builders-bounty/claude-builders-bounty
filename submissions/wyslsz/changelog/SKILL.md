---
name: generate-changelog
description: Auto-generate a structured CHANGELOG.md from git history. Categorizes commits into Added / Fixed / Changed / Removed since the last git tag. Use `/generate-changelog` or run `bash changelog.sh`.
version: 1.0.0
---

# Generate Changelog

Generate a structured, Keep-a-Changelog-style CHANGELOG.md from a project's git history.

## Trigger

Type `/generate-changelog` in Claude Code, or run the companion script directly:

```bash
bash changelog.sh [output-file] [repo-path]
```

## What it does

1. **Finds the last git tag** — uses `git describe --tags --abbrev=0`
2. **Collects all commits** since that tag (excluding merge commits)
3. **Auto-categorizes** each commit into:
   - **Added** — commits starting with `feat:`, `add:`, `new:`, `implement:`, `create:`, `introduce:`
   - **Fixed** — commits starting with `fix:`, `bug:`, `patch:`, `resolve:`, `hotfix:`, `correct:`
   - **Removed** — commits starting with `remove:`, `delete:`, `drop:`, `deprecate:`, `kill:`
   - **Changed** — everything else (refactors, docs, chores, etc.)
4. **Writes CHANGELOG.md** in standard Keep-a-Changelog format
5. Falls back to the first commit if no tags exist

## When to use

- Before a release — generates the release notes automatically
- After a sprint — summarizes what the team shipped
- For open source — keeps contributors and users informed

## How Claude Code should execute

When the user types `/generate-changelog`:

1. Run the companion script: `bash changelog.sh`
2. If the script succeeds, show a summary of what was generated
3. If there are no new commits, tell the user
4. The generated file is `CHANGELOG.md` in the repo root

## Example output

```markdown
# Changelog

## [v1.2.0 → HEAD] — 2025-06-15

> 12 commits since `v1.2.0`

### Added
- feat: add user authentication with JWT
- add rate limiting middleware
- new: dark mode toggle

### Fixed
- fix: resolve race condition in WebSocket handler
- bug: correct timezone offset in date picker

### Changed
- refactor: extract validation logic to shared module
- docs: update API reference for v2 endpoints
```

## Edge cases handled

- **No tags**: Uses the first commit as the starting point
- **No new commits**: Exits cleanly with a message
- **Empty repo**: Graceful error message
- **Merge commits**: Filtered out automatically
- **Non-standard commit messages**: Fall into "Changed" category
