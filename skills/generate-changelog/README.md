# generate-changelog

Generate a structured `CHANGELOG.md` from a project's git history.

Commits are auto-categorized into **Added**, **Fixed**, **Changed**, or **Removed** based on conventional commit keywords.

## Setup

1. Place this folder in your project as `skills/generate-changelog/`
2. Run `python skills/generate-changelog/changelog.py`
3. Open `CHANGELOG.md`

## Example output

```markdown
# Changelog

Generated from 42 commit(s)

## Added
- feat: add user authentication (abc12345)

## Fixed
- fix: resolve memory leak in cache layer (def67890)

## Changed
- refactor: migrate config to pydantic v2 (ghi01234)

## Removed
- remove: deprecated v1 API endpoints (jkl34567)
```
