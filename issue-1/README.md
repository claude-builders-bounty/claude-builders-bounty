# Auto Changelog Generator

A script to automatically generate a `CHANGELOG.md` file based on your git commit history since the last tag. It automatically categorizes commits based on conventional commit prefixes (e.g. `feat`, `fix`, `refactor`).

## Setup

1. Copy `changelog.sh` into your project directory.
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `./changelog.sh` (or `bash changelog.sh`)

## Sample Output

```markdown
# Changelog

*Auto-generated changelog for recent commits.*

## Added
- Added new user authentication module
- feat: integrate Stripe billing

## Fixed
- fix: resolve race condition in database connection
- Bug: typo in README

## Changed
- refactor: move util functions to shared library
```
