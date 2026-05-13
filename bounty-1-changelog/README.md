# CHANGELOG Generator

One command to generate a structured `CHANGELOG.md` from your git history.

## Usage

```bash
bash changelog.sh
# or specify paths:
bash changelog.sh --repo /path/to/project --output CHANGELOG.md
```

## How it works

1. Finds the last git tag (or starts from first commit)
2. Fetches all commits since that tag
3. Auto-categorizes by conventional commit prefix:
   - `feat/add/new` → **Added**
   - `fix/bug/hotfix` → **Fixed**
   - `remove/drop/delete` → **Removed**
   - everything else → **Changed**
4. Outputs a clean `CHANGELOG.md`

## Example output

```markdown
# Changelog

## [v1.2.0] - 2026-05-14

### Added
- Add user authentication via OAuth
- Implement dark mode toggle

### Fixed
- Fix login redirect loop
- Resolve memory leak in WebSocket handler

### Changed
- Upgrade dependency lodash to v5
```

## Requirements

- `bash` and `git` — that's it.
